import boto3
import json
import time

REGION = 'ap-southeast-1'

iam = boto3.client('iam', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

# Add Bedrock invoke permission
print("Adding Bedrock InvokeModel permission...")
policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": "bedrock:InvokeModel",
        "Resource": "*"
    }]
}

try:
    iam.put_role_policy(RoleName='hcg-demo-bedrock-agent', PolicyName='BedrockInvoke', PolicyDocument=json.dumps(policy))
    print("✅ Permission added\n")
except Exception as e:
    print(f"⚠️  {str(e)[:100]}\n")

# Wait for KBs to be ACTIVE
kbs = {
    'hr': {'kb_id': 'H0LFPBHIAK', 'ds_id': 'RXMESFOATH'},
    'it': {'kb_id': 'X1VW7AMIK8', 'ds_id': 'WARYSMSQOG'},
    'finance': {'kb_id': '1MFT5GZYTT', 'ds_id': 'EXOONIPSFS'},
    'general': {'kb_id': 'BOLGBDCUAZ', 'ds_id': 'K2CNYAU2YO'}
}

print("Waiting for KBs to be ACTIVE...")
for _ in range(12):
    all_active = True
    for domain, data in kbs.items():
        try:
            kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=data['kb_id'])
            status = kb['knowledgeBase']['status']
            if status != 'ACTIVE':
                all_active = False
        except:
            all_active = False
    
    if all_active:
        print("✅ All KBs ACTIVE\n")
        break
    time.sleep(10)

# Start ingestion
print("Starting ingestion...\n")
results = {}

for domain, data in kbs.items():
    print(f"{domain.upper()}: {data['kb_id']}")
    try:
        resp = bedrock_agent.start_ingestion_job(knowledgeBaseId=data['kb_id'], dataSourceId=data['ds_id'])
        job_id = resp['ingestionJob']['ingestionJobId']
        print(f"  🔄 Job: {job_id}")
        
        for _ in range(20):
            status_resp = bedrock_agent.get_ingestion_job(knowledgeBaseId=data['kb_id'], dataSourceId=data['ds_id'], ingestionJobId=job_id)
            status = status_resp['ingestionJob']['status']
            if status == 'COMPLETE':
                stats = status_resp['ingestionJob']['statistics']
                print(f"  ✅ {stats.get('numberOfDocumentsScanned', 0)} docs\n")
                results[domain] = {
                    'knowledge_base_id': data['kb_id'],
                    'data_source_id': data['ds_id'],
                    'ingestion_job_id': job_id
                }
                break
            elif status == 'FAILED':
                print(f"  ❌ Failed\n")
                break
            time.sleep(10)
    except Exception as e:
        print(f"  ❌ {str(e)[:150]}\n")

with open('hcg_demo_knowledge_bases.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"✅ {len(results)}/4 Knowledge Bases synced")
