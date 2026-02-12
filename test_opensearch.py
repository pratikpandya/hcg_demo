import boto3
import json
import requests
from requests_aws4auth import AWS4Auth

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

OPENSEARCH_COLLECTION_ID = resources['opensearch']['collection_id']
OPENSEARCH_ENDPOINT = f"https://{OPENSEARCH_COLLECTION_ID}.{REGION}.aoss.amazonaws.com"

# Get AWS credentials
session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    'aoss',
    session_token=credentials.token
)

# Test connection
print(f"Testing OpenSearch connection to: {OPENSEARCH_ENDPOINT}")

try:
    response = requests.get(OPENSEARCH_ENDPOINT, auth=awsauth, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Try to create an index
index_name = "hcg-demo-hr-idx"
index_url = f"{OPENSEARCH_ENDPOINT}/{index_name}"

index_body = {
    "settings": {
        "index.knn": True
    },
    "mappings": {
        "properties": {
            "vector": {
                "type": "knn_vector",
                "dimension": 1536
            },
            "text": {"type": "text"},
            "metadata": {"type": "text"}
        }
    }
}

print(f"\nCreating index: {index_name}")
try:
    response = requests.put(index_url, auth=awsauth, json=index_body, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
