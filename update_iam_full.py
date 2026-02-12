import boto3
import json
import time

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']
COLLECTION_ID = resources['opensearch']['collection_id']

iam = boto3.client('iam', region_name=REGION)
role_name = 'hcg-demo-bedrock-agent'

# Comprehensive policy
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [f"arn:aws:s3:::{S3_BUCKET}", f"arn:aws:s3:::{S3_BUCKET}/*"]
        },
        {
            "Effect": "Allow",
            "Action": ["aoss:APIAccessAll"],
            "Resource": f"arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/{COLLECTION_ID}"
        },
        {
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": f"arn:aws:bedrock:{REGION}::foundation-model/*"
        }
    ]
}

print(f"Updating {role_name} with comprehensive permissions...")
try:
    iam.put_role_policy(RoleName=role_name, PolicyName='BedrockKBFullAccess', PolicyDocument=json.dumps(policy))
    print("✅ Policy updated")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nWaiting 30 seconds for IAM propagation...")
time.sleep(30)
print("✅ Ready")
