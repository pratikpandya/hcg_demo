import boto3
import json
import subprocess
import time

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']
COLLECTION_ID = resources['opensearch']['collection_id']
ENDPOINT = f"https://{COLLECTION_ID}.{REGION}.aoss.amazonaws.com"
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"

bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

CONFIGS = {
    'hr': {'name': 'HCG-Demo-HR-KB', 'desc': 'HR policies', 's3_prefix': 'hr-docs/', 'index': 'hcg-kb-hr'},
    'it': {'name': 'HCG-Demo-IT-KB', 'desc': 'IT support', 's3_prefix': 'it-docs/', 'index': 'hcg-kb-it'},
    'finance': {'name': 'HCG-Demo-Finance-KB', 'desc': 'Finance', 's3_prefix': 'finance-docs/', 'index': 'hcg-kb-finance'},
    'general': {'name': 'HCG-Demo-General-KB', 'desc': 'General', 's3_prefix': 'general-docs/', 'index': 'hcg-kb-general'}
}

def create_index(index_name):
    """Create OpenSearch index using AWS CLI"""
    print(f"  Creating index: {index_name}...")
    
    index_body = {
        "settings": {"index.knn": True},
        "mappings": {
            "properties": {
                "vector": {"type": "knn_vector", "dimension": 1536},
                "text": {"type": "text"},
                "metadata": {"type": "text"}
            }
        }
    }
    
    cmd = [
        'aws', 'opensearchserverless', 'batch-get-collection',
        '--ids', COLLECTION_ID,
        '--region', REGION
    ]
    
    # Use curl with AWS sigv4 via Python requests instead
    import requests
    from requests_aws4auth import AWS4Auth
    
    session = boto3.Session()
    credentials = session.get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'aoss', session_token=credentials.token)
    
    url = f"{ENDPOINT}/{index_name}"
    
    try:
        response = requests.put(url, auth=awsauth, json=index_body, verify=False, timeout=30)
        if response.status_code in [200, 201]:
            print(f"  ✅ Index created")
            return True
        else:
            print(f"  ⚠️  Status {response.status_code}: {response.text[:100]}")
            return True  # May already exist
    except Exception as e:
        print(f"  ⚠️  {str(e)[:100]}")
        return True  # Continue anyway

def create_kb(domain, config):
    print(f"\n🧠 Creating {domain.upper()} Knowledge Base...")
    
    try:
        resp = bedrock_agent.create_knowledge_base(
            name=config['name'],
            description=config['desc'],
            roleArn=KB_ROLE_ARN,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v1'
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
        print(f"✅ KB: {kb_id}")
        time.sleep(3)
        return kb_id, resp['knowledgeBase']['knowledgeBaseArn']
    except Exception as e:
        print(f"❌ {str(e)[:200]}")
        return None, None

def create_ds(kb_id, config):
    print(f"📊 Creating data source...")
    try:
        resp = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f'{config["name"]}-DS',
            dataSourceConfiguration={'type': 'S3', 's3Configuration': {'bucketArn': f'arn:aws:s3:::{S3_BUCKET}', 'inclusionPrefixes': [config['s3_prefix']]}}
        )
        ds_id = resp['dataSource']['dataSourceId']
        print(f"✅ DS: {ds_id}")
        return ds_id
    except Exception as e:
        print(f"❌ {str(e)[:150]}")
        return None

def ingest(kb_id, ds_id):
    print(f"🔄 Ingesting...")
    try:
        resp = bedrock_agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
        job_id = resp['ingestionJob']['ingestionJobId']
        
        for _ in range(20):
            status_resp = bedrock_agent.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id, ingestionJobId=job_id)
            status = status_resp['ingestionJob']['status']
            if status == 'COMPLETE':
                stats = status_resp['ingestionJob']['statistics']
                print(f"✅ Indexed {stats.get('numberOfDocumentsScanned', 0)} docs")
                return job_id
            elif status == 'FAILED':
                print(f"❌ Failed")
                return None
            time.sleep(10)
        print(f"⏱️ Timeout")
        return job_id
    except Exception as e:
        print(f"❌ {str(e)[:150]}")
        return None

print("="*70)
print("🚀 Creating Knowledge Bases with AWS CLI")
print("="*70)

results = {}

for domain, config in CONFIGS.items():
    print(f"\n{'='*70}")
    print(f"{domain.upper()}")
    print(f"{'='*70}")
    
    create_index(config['index'])
    
    kb_id, kb_arn = create_kb(domain, config)
    if not kb_id:
        continue
    
    ds_id = create_ds(kb_id, config)
    if not ds_id:
        continue
    
    job_id = ingest(kb_id, ds_id)
    
    results[domain] = {
        'knowledge_base_id': kb_id,
        'knowledge_base_arn': kb_arn,
        'data_source_id': ds_id,
        'ingestion_job_id': job_id,
        'index_name': config['index']
    }

with open('hcg_demo_knowledge_bases.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*70}")
print(f"✅ Created {len(results)}/4 Knowledge Bases")
print(f"{'='*70}")
for domain, r in results.items():
    print(f"{domain.upper()}: {r['knowledge_base_id']}")
