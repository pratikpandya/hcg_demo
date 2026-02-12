import boto3
import json
import zipfile
import io
import time

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

lambda_client = boto3.client('lambda', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)

with open('hcg_demo_agents.json', 'r') as f:
    agents = json.load(f)

IT_AGENT_ID = agents['hcg-demo-it-agent']

print("="*70)
print("🚀 Deploying ServiceNow Integration")
print("="*70 + "\n")

# 1. Create Lambda package
print("1. Creating Lambda package...")
with open('lambda_servicenow_action.py', 'r') as f:
    code = f.read()

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('lambda_function.py', code)
zip_buffer.seek(0)
print("   ✅ Package created\n")

# 2. Deploy Lambda
print("2. Deploying Lambda...")
function_name = 'hcg-demo-servicenow-action'

try:
    lambda_client.get_function(FunctionName=function_name)
    lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_buffer.read()
    )
    print(f"   ✅ Updated: {function_name}\n")
    zip_buffer.seek(0)
except lambda_client.exceptions.ResourceNotFoundException:
    lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.11',
        Role=f'arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-lambda-bedrock',
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=60,
        MemorySize=256,
        Environment={'Variables': {'REGION': REGION}}
    )
    print(f"   ✅ Created: {function_name}\n")
    time.sleep(5)

# Get Lambda ARN
lambda_arn = lambda_client.get_function(FunctionName=function_name)['Configuration']['FunctionArn']

# 3. Add Lambda permission for Bedrock
print("3. Adding Bedrock invoke permission...")
try:
    lambda_client.add_permission(
        FunctionName=function_name,
        StatementId='AllowBedrockInvoke',
        Action='lambda:InvokeFunction',
        Principal='bedrock.amazonaws.com',
        SourceArn=f'arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/{IT_AGENT_ID}'
    )
    print("   ✅ Permission added\n")
except lambda_client.exceptions.ResourceConflictException:
    print("   ✅ Permission already exists\n")

# 4. Create Action Group schema
print("4. Creating Action Group...")

action_group_schema = {
    "openapi": "3.0.0",
    "info": {
        "title": "ServiceNow API",
        "version": "1.0.0",
        "description": "ServiceNow incident management"
    },
    "paths": {
        "/create_incident": {
            "post": {
                "summary": "Create a ServiceNow incident ticket",
                "description": "Create a new incident in ServiceNow",
                "operationId": "createIncident",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "short_description": {
                                        "type": "string",
                                        "description": "Brief description of the issue"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Detailed description"
                                    },
                                    "caller_id": {
                                        "type": "string",
                                        "description": "User ID"
                                    }
                                },
                                "required": ["short_description", "description"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Incident created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "incident_number": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/get_incident_status": {
            "post": {
                "summary": "Get status of a ServiceNow incident",
                "description": "Retrieve incident status",
                "operationId": "getIncidentStatus",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "incident_number": {
                                        "type": "string",
                                        "description": "Incident number"
                                    }
                                },
                                "required": ["incident_number"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Status retrieved",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "state": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

try:
    response = bedrock_agent.create_agent_action_group(
        agentId=IT_AGENT_ID,
        agentVersion='DRAFT',
        actionGroupName='ServiceNowActions',
        description='Create and track ServiceNow incidents',
        actionGroupExecutor={
            'lambda': lambda_arn
        },
        apiSchema={
            'payload': json.dumps(action_group_schema)
        }
    )
    
    action_group_id = response['agentActionGroup']['actionGroupId']
    print(f"   ✅ Action Group created: {action_group_id}\n")
    
except Exception as e:
    if 'already exists' in str(e).lower():
        print("   ✅ Action Group already exists\n")
    else:
        print(f"   ❌ Error: {str(e)[:150]}\n")

# 5. Prepare agent
print("5. Preparing IT agent...")
try:
    bedrock_agent.prepare_agent(agentId=IT_AGENT_ID)
    print("   ✅ Agent prepared\n")
except Exception as e:
    print(f"   ⚠️  {str(e)[:100]}\n")

print("="*70)
print("✅ ServiceNow Integration Deployed")
print("="*70)
print(f"\nLambda: {function_name}")
print(f"Action Group attached to IT Agent: {IT_AGENT_ID}")
print("\nCapabilities:")
print("  - Create ServiceNow incidents")
print("  - Track incident status")
print("  - OAuth token management")
print("  - User impersonation (X-UserToken)")
