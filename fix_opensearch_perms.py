import boto3
import json

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

COLLECTION_NAME = resources['opensearch']['collection_name']
COLLECTION_ID = resources['opensearch']['collection_id']

aoss = boto3.client('opensearchserverless', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)

identity = sts.get_caller_identity()
current_arn = identity['Arn']

print(f"Current user: {current_arn}")
print(f"Collection: {COLLECTION_NAME} ({COLLECTION_ID})\n")

# 1. Check network policy
print("1. Network Policy")
try:
    net_policies = aoss.list_security_policies(type='network')
    net_policy = [p for p in net_policies['securityPolicySummaries'] if COLLECTION_NAME in p['name']]
    if net_policy:
        print(f"   ✅ Exists: {net_policy[0]['name']}")
    else:
        print(f"   ❌ Not found")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Check encryption policy
print("\n2. Encryption Policy")
try:
    enc_policies = aoss.list_security_policies(type='encryption')
    enc_policy = [p for p in enc_policies['securityPolicySummaries'] if COLLECTION_NAME in p['name']]
    if enc_policy:
        print(f"   ✅ Exists: {enc_policy[0]['name']}")
    else:
        print(f"   ❌ Not found")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Fix data access policy
print("\n3. Data Access Policy")
policy_name = "hcg-demo-data-access"

try:
    current = aoss.get_access_policy(name=policy_name, type='data')
    policy_version = current['accessPolicyDetail']['policyVersion']
    print(f"   Current version: {policy_version}")
    
    # Comprehensive policy with all permissions
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
            "Principal": list(set([
                f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent",
                f"arn:aws:sts::{ACCOUNT_ID}:assumed-role/hcg-demo-bedrock-agent/*",
                current_arn
            ]))
        }
    ]
    
    response = aoss.update_access_policy(
        name=policy_name,
        type='data',
        policyVersion=policy_version,
        policy=json.dumps(policy_document)
    )
    print(f"   ✅ Updated with all principals")
    print(f"   New version: {response['accessPolicyDetail']['policyVersion']}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n4. Waiting 30 seconds for policy propagation...")
import time
time.sleep(30)
print("   ✅ Done")
