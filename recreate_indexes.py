import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import time
import urllib3
urllib3.disable_warnings()

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

COLLECTION_ID = resources['opensearch']['collection_id']
ENDPOINT = f"https://{COLLECTION_ID}.{REGION}.aoss.amazonaws.com"

session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'aoss', session_token=credentials.token)

bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

INDEXES = ['hcg-kb-hr', 'hcg-kb-it', 'hcg-kb-finance', 'hcg-kb-general']

# Delete existing indexes
print("Deleting existing indexes...")
for index in INDEXES:
    try:
        response = requests.delete(f"{ENDPOINT}/{index}", auth=awsauth, verify=False, timeout=10)
        print(f"  {index}: {response.status_code}")
    except Exception as e:
        print(f"  {index}: {str(e)[:50]}")

time.sleep(5)

# Create indexes with Bedrock-compatible settings
print("\nCreating Bedrock-compatible indexes...")

index_body = {
    "settings": {
        "index.knn": True,
        "index.knn.algo_param.ef_search": 512
    },
    "mappings": {
        "properties": {
            "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
            "AMAZON_BEDROCK_METADATA": {"type": "text"},
            "bedrock-knowledge-base-default-vector": {
                "type": "knn_vector",
                "dimension": 1536,
                "method": {
                    "name": "hnsw",
                    "engine": "faiss",
                    "parameters": {}
                }
            }
        }
    }
}

for index in INDEXES:
    try:
        response = requests.put(f"{ENDPOINT}/{index}", auth=awsauth, json=index_body, verify=False, timeout=30)
        if response.status_code in [200, 201]:
            print(f"  ✅ {index}")
        else:
            print(f"  ❌ {index}: {response.status_code}")
    except Exception as e:
        print(f"  ❌ {index}: {str(e)[:50]}")

print("\nWaiting 10 seconds for indexes to be ready...")
time.sleep(10)
print("✅ Done")
