import boto3
import json
import time
from pathlib import Path

# Configuration
REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

# Load resources
with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']
OPENSEARCH_COLLECTION_ID = resources['opensearch']['collection_id']
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"

# Initialize clients
s3 = boto3.client('s3', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

KB_CONFIGS = {
    'hr': {
        'name': 'HCG-Demo-HR-KB',
        'description': 'HR policies, benefits, leave, and onboarding',
        'folder': 'sample_documents/hr',
        's3_prefix': 'hr-docs/',
        'index': 'hcg-demo-hr-idx'
    },
    'it': {
        'name': 'HCG-Demo-IT-KB',
        'description': 'IT support, software, VPN, troubleshooting',
        'folder': 'sample_documents/it',
        's3_prefix': 'it-docs/',
        'index': 'hcg-demo-it-idx'
    },
    'finance': {
        'name': 'HCG-Demo-Finance-KB',
        'description': 'Finance policies, procurement, expenses',
        'folder': 'sample_documents/finance',
        's3_prefix': 'finance-docs/',
        'index': 'hcg-demo-finance-idx'
    },
    'general': {
        'name': 'HCG-Demo-General-KB',
        'description': 'Company info, office locations, FAQs',
        'folder': 'sample_documents/general',
        's3_prefix': 'general-docs/',
        'index': 'hcg-demo-general-idx'
    }
}

def upload_documents(domain, config):
    print(f"📤 Uploading {domain.upper()} documents...")
    folder_path = Path(config['folder'])
    count = 0
    
    for file_path in folder_path.glob('*.txt'):
        s3_key = f"{config['s3_prefix']}{file_path.name}"
        s3.upload_file(str(file_path), S3_BUCKET, s3_key, ExtraArgs={'ContentType': 'text/plain'})
        print(f"  ✓ {file_path.name}")
        count += 1
    
    print(f"✅ Uploaded {count} documents\n")
    return count

def create_kb(domain, config):
    print(f"🧠 Creating {domain.upper()} Knowledge Base...")
    
    try:
        response = bedrock_agent.create_knowledge_base(
            name=config['name'],
            description=config['description'],
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
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        kb_arn = response['knowledgeBase']['knowledgeBaseArn']
        print(f"✅ KB created: {kb_id}\n")
        time.sleep(5)
        return kb_id, kb_arn
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}\n")
        return None, None

def create_datasource(kb_id, config):
    print(f"📊 Creating data source...")
    
    try:
        response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f'{config["name"]}-DS',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{S3_BUCKET}',
                    'inclusionPrefixes': [config['s3_prefix']]
                }
            }
        )
        
        ds_id = response['dataSource']['dataSourceId']
        print(f"✅ Data source: {ds_id}\n")
        return ds_id
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}\n")
        return None

def ingest(kb_id, ds_id):
    print(f"🔄 Starting ingestion...")
    
    try:
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"  Job ID: {job_id}")
        print(f"  Waiting for completion...")
        
        while True:
            status_resp = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id
            )
            
            status = status_resp['ingestionJob']['status']
            
            if status == 'COMPLETE':
                stats = status_resp['ingestionJob']['statistics']
                print(f"✅ Complete! Docs indexed: {stats.get('numberOfDocumentsScanned', 0)}\n")
                break
            elif status == 'FAILED':
                print(f"❌ Failed\n")
                break
            else:
                time.sleep(15)
        
        return job_id
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}\n")
        return None

def main():
    print("=" * 70)
    print("🚀 HCG Demo - Knowledge Base Setup")
    print("=" * 70 + "\n")
    
    results = {}
    
    for domain, config in KB_CONFIGS.items():
        print(f"{'=' * 70}")
        print(f"{domain.upper()} Knowledge Base")
        print(f"{'=' * 70}\n")
        
        doc_count = upload_documents(domain, config)
        if doc_count == 0:
            continue
        
        kb_id, kb_arn = create_kb(domain, config)
        if not kb_id:
            continue
        
        ds_id = create_datasource(kb_id, config)
        if not ds_id:
            continue
        
        job_id = ingest(kb_id, ds_id)
        
        results[domain] = {
            'knowledge_base_id': kb_id,
            'knowledge_base_arn': kb_arn,
            'data_source_id': ds_id,
            'ingestion_job_id': job_id,
            'document_count': doc_count,
            's3_prefix': config['s3_prefix'],
            'index_name': config['index']
        }
    
    with open('hcg_demo_knowledge_bases.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70 + "\n")
    
    for domain, r in results.items():
        print(f"{domain.upper()}: {r['knowledge_base_id']} ({r['document_count']} docs)")

if __name__ == '__main__':
    main()
