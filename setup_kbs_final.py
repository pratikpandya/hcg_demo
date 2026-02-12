import boto3
import json
import time
import urllib3
from pathlib import Path

# Disable SSL warnings for OpenSearch Serverless
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']
OPENSEARCH_COLLECTION_ID = resources['opensearch']['collection_id']
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"

s3 = boto3.client('s3', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

KB_CONFIGS = {
    'hr': {'name': 'HCG-Demo-HR-KB', 'desc': 'HR policies', 'folder': 'sample_documents/hr', 's3_prefix': 'hr-docs/', 'index': 'bedrock-knowledge-base-default-index'},
    'it': {'name': 'HCG-Demo-IT-KB', 'desc': 'IT support', 'folder': 'sample_documents/it', 's3_prefix': 'it-docs/', 'index': 'bedrock-knowledge-base-default-index'},
    'finance': {'name': 'HCG-Demo-Finance-KB', 'desc': 'Finance policies', 'folder': 'sample_documents/finance', 's3_prefix': 'finance-docs/', 'index': 'bedrock-knowledge-base-default-index'},
    'general': {'name': 'HCG-Demo-General-KB', 'desc': 'Company info', 'folder': 'sample_documents/general', 's3_prefix': 'general-docs/', 'index': 'bedrock-knowledge-base-default-index'}
}

def upload_docs(domain, config):
    print(f"📤 Uploading {domain.upper()}...")
    count = 0
    for file in Path(config['folder']).glob('*.txt'):
        s3.upload_file(str(file), S3_BUCKET, f"{config['s3_prefix']}{file.name}", ExtraArgs={'ContentType': 'text/plain'})
        count += 1
    print(f"✅ {count} docs\n")
    return count

def create_kb(domain, config):
    print(f"🧠 Creating KB...")
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
                    'collectionArn': f"arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/{OPENSEARCH_COLLECTION_ID}",
                    'vectorIndexName': config['index'],
                    'fieldMapping': {'vectorField': 'bedrock-knowledge-base-default-vector', 'textField': 'AMAZON_BEDROCK_TEXT_CHUNK', 'metadataField': 'AMAZON_BEDROCK_METADATA'}
                }
            }
        )
        kb_id = resp['knowledgeBase']['knowledgeBaseId']
        print(f"✅ {kb_id}\n")
        time.sleep(3)
        return kb_id, resp['knowledgeBase']['knowledgeBaseArn']
    except Exception as e:
        print(f"❌ {str(e)[:200]}\n")
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
        print(f"✅ {ds_id}\n")
        return ds_id
    except Exception as e:
        print(f"❌ {str(e)[:150]}\n")
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
                print(f"✅ Indexed {stats.get('numberOfDocumentsScanned', 0)} docs\n")
                return job_id
            elif status == 'FAILED':
                print(f"❌ Failed\n")
                return None
            time.sleep(10)
        print(f"⏱️ Timeout\n")
        return job_id
    except Exception as e:
        print(f"❌ {str(e)[:150]}\n")
        return None

def main():
    print("="*70)
    print("🚀 HCG Demo - Knowledge Base Setup")
    print("="*70 + "\n")
    
    results = {}
    
    for domain, config in KB_CONFIGS.items():
        print(f"{domain.upper()}")
        print("-"*70)
        
        count = upload_docs(domain, config)
        if count == 0:
            continue
        
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
            'document_count': count
        }
    
    with open('hcg_demo_knowledge_bases.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("="*70)
    print(f"✅ Created {len(results)} Knowledge Bases")
    print("="*70)
    for domain, r in results.items():
        print(f"{domain.upper()}: {r['knowledge_base_id']}")

if __name__ == '__main__':
    main()
