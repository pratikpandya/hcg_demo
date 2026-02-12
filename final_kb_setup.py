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

S3_BUCKET = resources['s3']['knowledge']
COLLECTION_ID = resources['opensearch']['collection_id']
ENDPOINT = f"https://{COLLECTION_ID}.{REGION}.aoss.amazonaws.com"
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"

session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'aoss', session_token=credentials.token)

bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

CONFIGS = {
    'hr': {'name': 'HCG-Demo-HR-KB', 'desc': 'HR policies', 's3_prefix': 'hr-docs/', 'index': 'hcg-kb-hr'},
    'it': {'name': 'HCG-Demo-IT-KB', 'desc': 'IT support', 's3_prefix': 'it-docs/', 'index': 'hcg-kb-it'},
    'finance': {'name': 'HCG-Demo-Finance-KB', 'desc': 'Finance', 's3_prefix': 'finance-docs/', 'index': 'hcg-kb-finance'},
    'general': {'name': 'HCG-Demo-General-KB', 'desc': 'General', 's3_prefix': 'general-docs/', 'index': 'hcg-kb-general'}
}

# Delete and recreate indexes with Cohere dimension (1024)
print("Recreating indexes for Cohere (dimension 1024)...\n")

index_body = {
    "settings": {"index.knn": True},
    "mappings": {
        "properties": {
            "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
            "AMAZON_BEDROCK_METADATA": {"type": "text"},
            "bedrock-knowledge-base-default-vector": {
                "type": "knn_vector",
                "dimension": 1024,
                "method": {"name": "hnsw", "engine": "faiss"}
            }
        }
    }
}

for domain, config in CONFIGS.items():
    idx = config['index']
    requests.delete(f"{ENDPOINT}/{idx}", auth=awsauth, verify=False, timeout=10)
    time.sleep(2)
    resp = requests.put(f"{ENDPOINT}/{idx}", auth=awsauth, json=index_body, verify=False, timeout=30)
    print(f"  {idx}: {resp.status_code}")

print("\nWaiting 10 seconds...")
time.sleep(10)

# Create KBs
print("\nCreating Knowledge Bases...\n")

results = {}

for domain, config in CONFIGS.items():
    print(f"{domain.upper()}")
    try:
        resp = bedrock_agent.create_knowledge_base(
            name=config['name'],
            description=config['desc'],
            roleArn=KB_ROLE_ARN,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{REGION}::foundation-model/cohere.embed-multilingual-v3'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': f"arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/{COLLECTION_ID}",
                    'vectorIndexName': config['index'],
                    'fieldMapping': {'vectorField': 'bedrock-knowledge-base-default-vector', 'textField': 'AMAZON_BEDROCK_TEXT_CHUNK', 'metadataField': 'AMAZON_BEDROCK_METADATA'}
                }
            }
        )
        kb_id = resp['knowledgeBase']['knowledgeBaseId']
        print(f"  ✅ KB: {kb_id}")
        
        ds_resp = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f'{config["name"]}-DS',
            dataSourceConfiguration={'type': 'S3', 's3Configuration': {'bucketArn': f'arn:aws:s3:::{S3_BUCKET}', 'inclusionPrefixes': [config['s3_prefix']]}}
        )
        ds_id = ds_resp['dataSource']['dataSourceId']
        print(f"  ✅ DS: {ds_id}")
        
        job_resp = bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
        job_id = job_resp['ingestionJob']['ingestionJobId']
        print(f"  🔄 Job: {job_id}")
        
        for _ in range(20):
            status_resp = bedrock_agent.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id, ingestionJobId=job_id)
            status = status_resp['ingestionJob']['status']
            if status == 'COMPLETE':
                stats = status_resp['ingestionJob']['statistics']
                print(f"  ✅ {stats.get('numberOfDocumentsScanned', 0)} docs indexed\n")
                break
            elif status == 'FAILED':
                print(f"  ❌ Failed\n")
                break
            time.sleep(10)
        
        results[domain] = {
            'knowledge_base_id': kb_id,
            'knowledge_base_arn': resp['knowledgeBase']['knowledgeBaseArn'],
            'data_source_id': ds_id,
            'ingestion_job_id': job_id,
            'index_name': config['index']
        }
        
    except Exception as e:
        print(f"  ❌ {str(e)[:200]}\n")

with open('hcg_demo_knowledge_bases.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"✅ {len(results)}/4 Knowledge Bases created and synced")
