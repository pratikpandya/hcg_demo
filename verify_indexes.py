import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
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

print("Checking created indexes...\n")

for index in ['hcg-kb-hr', 'hcg-kb-it', 'hcg-kb-finance', 'hcg-kb-general']:
    url = f"{ENDPOINT}/{index}"
    try:
        response = requests.get(url, auth=awsauth, verify=False, timeout=10)
        if response.status_code == 200:
            print(f"✅ {index}: EXISTS")
            data = response.json()
            if index in data:
                mappings = data[index].get('mappings', {})
                print(f"   Mappings: {json.dumps(mappings, indent=2)[:200]}")
        else:
            print(f"❌ {index}: {response.status_code}")
    except Exception as e:
        print(f"❌ {index}: {str(e)[:100]}")
    print()

# Try listing all indexes
print("\nListing all indexes:")
try:
    response = requests.get(f"{ENDPOINT}/_cat/indices?format=json", auth=awsauth, verify=False, timeout=10)
    if response.status_code == 200:
        indexes = response.json()
        for idx in indexes:
            print(f"  - {idx.get('index', 'unknown')}")
    else:
        print(f"  Status: {response.status_code}")
except Exception as e:
    print(f"  Error: {str(e)[:100]}")
