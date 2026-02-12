import boto3
import json
import time
from pathlib import Path
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Configuration
REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

# Load existing resources
with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']
OPENSEARCH_COLLECTION_ID = resources['opensearch']['collection_id']
OPENSEARCH_ENDPOINT = f"{OPENSEARCH_COLLECTION_ID}.{REGION}.aoss.amazonaws.com"
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"

# Initialize clients
s3 = boto3.client('s3', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'aoss', session_token=credentials.token)

# OpenSearch client
os_client = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

KB_CONFIGS = {
    'hr': {
        'name': 'HCG-Demo-HR-KB',
        'description': 'HR policies, benefits, leave, and onboarding information',
        'folder': 'sample_documents/hr',
        's3_prefix': 'hr-docs/',
        'index': 'hcg-demo-hr-index'
    },
    'it': {
        'name': 'HCG-Demo-IT-KB',
        'description': 'IT support guides, software installation, VPN, and troubleshooting',
        'folder': 'sample_documents/it',
        's3_prefix': 'it-docs/',
        'index': 'hcg-demo-it-index'
    },
    'finance': {
        'name': 'HCG-Demo-Finance-KB',
        'description': 'Finance policies, procurement, and expense reimbursement',
        'folder': 'sample_documents/finance',
        's3_prefix': 'finance-docs/',
        'index': 'hcg-demo-finance-index'
    },
    'general': {
        'name': 'HCG-Demo-General-KB',
        'description': 'General company information, office locations, and FAQs',
        'folder': 'sample_documents/general',
        's3_prefix': 'general-docs/',
        'index': 'hcg-demo-general-index'
    }
}

def create_opensearch_index(index_name):
    """Create OpenSearch index for Knowledge Base"""
    print(f"  Creating OpenSearch index: {index_name}...")
    
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 2,
                "number_of_replicas": 0
            }
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "engine": "faiss"
                    }
                },
                "text": {"type": "text"},
                "metadata": {"type": "text"}
            }
        }
    }
    
    try:
        if os_client.indices.exists(index=index_name):
            print(f"  ✅ Index {index_name} already exists")
            return True
        
        os_client.indices.create(index=index_name, body=index_body)
        print(f"  ✅ Index {index_name} created")
        return True
    except Exception as e:
        print(f"  ❌ Error creating index: {e}")
        return False

def upload_documents_to_s3(domain, config):
    """Upload documents from local folder to S3"""
    print(f"📤 Uploading {domain.upper()} documents to S3...")
    
    folder_path = Path(config['folder'])
    s3_prefix = config['s3_prefix']
    uploaded_count = 0
    
    if not folder_path.exists():
        print(f"  ⚠️ Folder not found: {folder_path}")
        return 0
    
    for file_path in folder_path.glob('*.txt'):
        s3_key = f"{s3_prefix}{file_path.name}"
        print(f"  Uploading {file_path.name}...")
        
        s3.upload_file(
            str(file_path),
            S3_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': 'text/plain'}
        )
        uploaded_count += 1
    
    print(f"✅ Uploaded {uploaded_count} documents")
    return uploaded_count

def create_knowledge_base(domain, config):
    """Create Bedrock Knowledge Base"""
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
        
        print(f"✅ Knowledge Base created: {kb_id}")
        time.sleep(5)
        
        return kb_id, kb_arn
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def create_data_source(kb_id, domain, config):
    """Create data source for Knowledge Base"""
    print(f"📊 Creating data source...")
    
    try:
        response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f'{config["name"]}-DataSource',
            description=f'S3 data source for {domain} documents',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{S3_BUCKET}',
                    'inclusionPrefixes': [config['s3_prefix']]
                }
            }
        )
        
        ds_id = response['dataSource']['dataSourceId']
        print(f"✅ Data source created: {ds_id}")
        
        return ds_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def start_ingestion_job(kb_id, ds_id, domain):
    """Start ingestion job to index documents"""
    print(f"🔄 Starting ingestion job...")
    
    try:
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"✅ Ingestion started: {job_id}")
        print("  Waiting for completion (2-3 minutes)...")
        
        while True:
            status_response = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id
            )
            
            status = status_response['ingestionJob']['status']
            
            if status == 'COMPLETE':
                stats = status_response['ingestionJob']['statistics']
                print(f"✅ Ingestion complete! Documents: {stats.get('numberOfDocumentsScanned', 0)}")
                break
            elif status == 'FAILED':
                print(f"❌ Ingestion failed")
                break
            else:
                time.sleep(20)
        
        return job_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("=" * 70)
    print("🚀 HCG Demo - Knowledge Base Setup")
    print("=" * 70)
    
    kb_results = {}
    
    for domain, config in KB_CONFIGS.items():
        print(f"\n{'=' * 70}")
        print(f"Processing {domain.upper()} Knowledge Base")
        print(f"{'=' * 70}\n")
        
        # Step 1: Create OpenSearch index
        if not create_opensearch_index(config['index']):
            print(f"⚠️ Skipping {domain}\n")
            continue
        
        # Step 2: Upload documents to S3
        doc_count = upload_documents_to_s3(domain, config)
        
        if doc_count == 0:
            print(f"⚠️ No documents to upload for {domain}\n")
            continue
        
        # Step 3: Create Knowledge Base
        kb_id, kb_arn = create_knowledge_base(domain, config)
        
        if not kb_id:
            print(f"⚠️ Skipping {domain}\n")
            continue
        
        # Step 4: Create Data Source
        ds_id = create_data_source(kb_id, domain, config)
        
        if not ds_id:
            print(f"⚠️ Skipping {domain}\n")
            continue
        
        # Step 5: Start Ingestion
        job_id = start_ingestion_job(kb_id, ds_id, domain)
        
        kb_results[domain] = {
            'knowledge_base_id': kb_id,
            'knowledge_base_arn': kb_arn,
            'data_source_id': ds_id,
            'ingestion_job_id': job_id,
            'document_count': doc_count,
            's3_prefix': config['s3_prefix'],
            'index_name': config['index']
        }
    
    # Save results
    with open('hcg_demo_knowledge_bases.json', 'w') as f:
        json.dump(kb_results, f, indent=2)
    
    print(f"\n{'=' * 70}")
    print("✅ Knowledge Base Setup Complete!")
    print(f"{'=' * 70}\n")
    
    print("📊 Summary:")
    for domain, result in kb_results.items():
        print(f"\n{domain.upper()}:")
        print(f"  KB ID: {result['knowledge_base_id']}")
        print(f"  Documents: {result['document_count']}")

if __name__ == '__main__':
    main()
