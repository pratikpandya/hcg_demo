import boto3
import json

REGION = 'ap-southeast-1'

iam = boto3.client('iam', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

role_name = 'hcg-demo-bedrock-agent'

# Check trust relationship
print("Checking IAM role trust relationship...")
try:
    role = iam.get_role(RoleName=role_name)
    trust_policy = role['Role']['AssumeRolePolicyDocument']
    print(json.dumps(trust_policy, indent=2))
    
    # Check if bedrock.amazonaws.com is in trust
    principals = []
    for statement in trust_policy.get('Statement', []):
        principal = statement.get('Principal', {})
        if 'Service' in principal:
            principals.extend(principal['Service'] if isinstance(principal['Service'], list) else [principal['Service']])
    
    if 'bedrock.amazonaws.com' in principals:
        print("\n✅ bedrock.amazonaws.com is trusted")
    else:
        print("\n❌ bedrock.amazonaws.com NOT in trust relationship")
        print("   Adding it now...")
        
        # Update trust policy
        trust_policy['Statement'].append({
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        })
        
        iam.update_assume_role_policy(
            RoleName=role_name,
            PolicyDocument=json.dumps(trust_policy)
        )
        print("   ✅ Trust relationship updated")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Try ingestion with full error
print("\n\nTrying ingestion to get full error...")
with open('hcg_demo_knowledge_bases.json', 'r') as f:
    kbs = json.load(f)

kb_id = kbs['hr']['knowledge_base_id']
ds_id = kbs['hr']['data_source_id']

try:
    resp = bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
    print(f"✅ Started: {resp['ingestionJob']['ingestionJobId']}")
except Exception as e:
    print(f"Full error: {str(e)}")
