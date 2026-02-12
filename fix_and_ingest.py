import boto3
import json
import time

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']

iam = boto3.client('iam', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

role_name = 'hcg-demo-bedrock-agent'

# Add S3 read permissions
s3_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [
                f"arn:aws:s3:::{S3_BUCKET}",
                f"arn:aws:s3:::{S3_BUCKET}/*"
            ]
        }
    ]
}

print(f"Adding S3 permissions to {role_name}...")
try:
    iam.put_role_policy(RoleName=role_name, PolicyName='BedrockS3Access', PolicyDocument=json.dumps(s3_policy))
    print("✅ S3 policy added\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Load KB IDs and retry ingestion
with open('hcg_demo_knowledge_bases.json', 'r') as f:
    kbs = json.load(f)

print("Retrying ingestion for all KBs...\n")

for domain, kb_data in kbs.items():
    kb_id = kb_data['knowledge_base_id']
    ds_id = kb_data['data_source_id']
    
    print(f"{domain.upper()}: {kb_id}")
    try:
        resp = bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
        job_id = resp['ingestionJob']['ingestionJobId']
        print(f"  🔄 Job: {job_id}")
        
        for _ in range(20):
            status_resp = bedrock_agent.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id, ingestionJobId=job_id)
            status = status_resp['ingestionJob']['status']
            if status == 'COMPLETE':
                stats = status_resp['ingestionJob']['statistics']
                print(f"  ✅ Indexed {stats.get('numberOfDocumentsScanned', 0)} docs\n")
                kb_data['ingestion_job_id'] = job_id
                break
            elif status == 'FAILED':
                print(f"  ❌ Failed\n")
                break
            time.sleep(10)
    except Exception as e:
        print(f"  ❌ {str(e)[:150]}\n")

# Save updated results
with open('hcg_demo_knowledge_bases.json', 'w') as f:
    json.dump(kbs, f, indent=2)

print("✅ Results saved to hcg_demo_knowledge_bases.json")
