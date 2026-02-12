import boto3
import json

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

iam = boto3.client('iam', region_name=REGION)

role_name = 'hcg-demo-bedrock-agent'

# Add OpenSearch policy
opensearch_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "aoss:APIAccessAll"
            ],
            "Resource": f"arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/*"
        }
    ]
}

print(f"Adding OpenSearch permissions to {role_name}...")

try:
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockOpenSearchAccess',
        PolicyDocument=json.dumps(opensearch_policy)
    )
    print("✅ Policy added")
except Exception as e:
    print(f"❌ Error: {e}")

# Wait and retry KB creation
print("\nWaiting 10 seconds...")
import time
time.sleep(10)
print("✅ Ready to retry")
