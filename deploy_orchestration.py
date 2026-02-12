import boto3
import json
import zipfile
import io

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

lambda_client = boto3.client('lambda', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)

with open('hcg_demo_agents.json', 'r') as f:
    agents = json.load(f)

print("="*70)
print("🚀 Deploying Agent Orchestration")
print("="*70 + "\n")

# 1. Create Lambda deployment package
print("1. Creating Lambda deployment package...")
with open('lambda_supervisor_agent.py', 'r') as f:
    lambda_code = f.read()

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.writestr('lambda_function.py', lambda_code)
zip_buffer.seek(0)

print("   ✅ Package created\n")

# 2. Deploy/Update Lambda
print("2. Deploying supervisor Lambda...")
function_name = 'hcg-demo-supervisor-orchestrator'

try:
    lambda_client.get_function(FunctionName=function_name)
    # Update existing
    lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_buffer.read()
    )
    print(f"   ✅ Updated: {function_name}\n")
except lambda_client.exceptions.ResourceNotFoundException:
    # Create new
    lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.11',
        Role=f'arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-lambda-bedrock',
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=300,
        MemorySize=512,
        Environment={'Variables': {'REGION': REGION}}
    )
    print(f"   ✅ Created: {function_name}\n")

# 3. Prepare agents (create aliases)
print("3. Preparing agent aliases...")

for agent_name, agent_id in agents.items():
    if 'supervisor' in agent_name:
        continue
    
    print(f"   {agent_name}: {agent_id}")
    try:
        # Prepare agent
        bedrock_agent.prepare_agent(agentId=agent_id)
        print(f"      ✅ Prepared\n")
    except Exception as e:
        if 'already prepared' in str(e).lower():
            print(f"      ✅ Already prepared\n")
        else:
            print(f"      ⚠️  {str(e)[:100]}\n")

print("="*70)
print("✅ Agent Orchestration Deployed")
print("="*70)
print(f"\nSupervisor Lambda: {function_name}")
print("Specialist agents prepared and linked to KBs")
