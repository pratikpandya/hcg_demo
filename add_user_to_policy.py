import boto3
import json

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

COLLECTION_NAME = resources['opensearch']['collection_name']

aoss = boto3.client('opensearchserverless', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)

# Get current user ARN
identity = sts.get_caller_identity()
current_arn = identity['Arn']
print(f"Current user: {current_arn}")

policy_name = "hcg-demo-data-access"

# Get current policy
current = aoss.get_access_policy(name=policy_name, type='data')
policy_version = current['accessPolicyDetail']['policyVersion']

# Update policy to include current user
policy_document = [
    {
        "Rules": [
            {
                "Resource": [f"collection/{COLLECTION_NAME}"],
                "Permission": ["aoss:*"],
                "ResourceType": "collection"
            },
            {
                "Resource": [f"index/{COLLECTION_NAME}/*"],
                "Permission": ["aoss:*"],
                "ResourceType": "index"
            }
        ],
        "Principal": [
            f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent",
            current_arn
        ]
    }
]

print(f"\nUpdating policy to include current user...")
try:
    response = aoss.update_access_policy(
        name=policy_name,
        type='data',
        policyVersion=policy_version,
        policy=json.dumps(policy_document)
    )
    print(f"✅ Policy updated")
except Exception as e:
    print(f"❌ Error: {e}")
