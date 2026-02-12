import boto3
import json

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

COLLECTION_NAME = resources['opensearch']['collection_name']

aoss = boto3.client('opensearchserverless', region_name=REGION)

# Update existing data access policy for Bedrock
policy_name = "hcg-demo-data-access"

policy_document = [
    {
        "Rules": [
            {
                "Resource": [f"collection/{COLLECTION_NAME}"],
                "Permission": [
                    "aoss:CreateCollectionItems",
                    "aoss:DeleteCollectionItems",
                    "aoss:UpdateCollectionItems",
                    "aoss:DescribeCollectionItems"
                ],
                "ResourceType": "collection"
            },
            {
                "Resource": [f"index/{COLLECTION_NAME}/*"],
                "Permission": [
                    "aoss:CreateIndex",
                    "aoss:DeleteIndex",
                    "aoss:UpdateIndex",
                    "aoss:DescribeIndex",
                    "aoss:ReadDocument",
                    "aoss:WriteDocument"
                ],
                "ResourceType": "index"
            }
        ],
        "Principal": [
            f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent",
            f"arn:aws:sts::{ACCOUNT_ID}:assumed-role/hcg-demo-bedrock-agent/*"
        ],
        "Description": "Data access for Bedrock Knowledge Bases"
    }
]

print(f"Updating data access policy: {policy_name}")
print(f"Collection: {COLLECTION_NAME}")
print(f"Principal: arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent")

try:
    # Get current policy
    current = aoss.get_access_policy(name=policy_name, type='data')
    policy_version = current['accessPolicyDetail']['policyVersion']
    print(f"Current policy version: {policy_version}")
    
    response = aoss.update_access_policy(
        name=policy_name,
        type='data',
        policyVersion=policy_version,
        policy=json.dumps(policy_document)
    )
    print(f"✅ Policy updated successfully")
except Exception as e:
    print(f"❌ Error: {e}")

# List existing policies
print("\n" + "="*70)
print("Existing data access policies:")
try:
    policies = aoss.list_access_policies(type='data')
    for policy in policies.get('accessPolicySummaries', []):
        print(f"  - {policy['name']}")
except Exception as e:
    print(f"Error listing policies: {e}")
