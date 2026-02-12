import boto3
import json
import time
from pathlib import Path

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/hcg-demo-bedrock-agent"

s3 = boto3.client('s3', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

KB_CONFIGS = {
    'hr': {
        'name': 'HCG-Demo-HR-KB',
        'description': 'HR policies, benefits, leave',
        'folder': 'sample_documents/hr',
        's3_prefix': 'hr-docs/'
    },
    'it': {
        'name': 'HCG-Demo-IT-KB',
        'description': 'IT support and troubleshooting',
        'folder': 'sample_documents/it',
        's3_prefix': 'it-docs/'
    },
    'finance': {
        'name': 'HCG-Demo-Finance-KB',
        'description': 'Finance policies and procedures',
        'folder': 'sample_documents/finance',
        's3_prefix': 'finance-docs/'
    },
    'general': {
        'name': 'HCG-Demo-General-KB',
        'description': 'General company information',
        'folder': 'sample_documents/general',
        's3_prefix': 'general-docs/'
    }
}

def upload_docs(domain, config):
    print(f"📤 Uploading {domain.upper()} documents...")
    folder = Path(config['folder'])
    count = 0
    
    for file in folder.glob('*.txt'):
        s3_key = f"{config['s3_prefix']}{file.name}"
        s3.upload_file(str(file), S3_BUCKET, s3_key, ExtraArgs={'ContentType': 'text/plain'})
        print(f"  ✓ {file.name}")
        count += 1
    
    print(f"✅ {count} documents uploaded\n")
    return count

def create_kb_pinecone_style(domain, config):
    """Create KB with managed vector store (no OpenSearch dependency)"""
    print(f"🧠 Creating {domain.upper()} Knowledge Base...")
    
    try:
        # Use VECTOR type without specifying OpenSearch - let Bedrock manage it
        response = bedrock_agent.create_knowledge_base(
            name=config['name'],
            description=config['description'],
            roleArn=KB_ROLE_ARN,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'PINECONE',
                'pineconeConfiguration': {
                    'connectionString': f's3://{S3_BUCKET}/{config["s3_prefix"]}',
                    'credentialsSecretArn': KB_ROLE_ARN,
                    'namespace': f'hcg-demo-{domain}',
                    'fieldMapping': {
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        kb_arn = response['knowledgeBase']['knowledgeBaseArn']
        print(f"✅ KB: {kb_id}\n")
        time.sleep(3)
        return kb_id, kb_arn
    except Exception as e:
        error_msg = str(e)
        if 'PINECONE' in error_msg:
            print(f"⚠️  Pinecone not supported, trying RDS Aurora...\n")
            return None, None
        print(f"❌ Error: {error_msg[:150]}\n")
        return None, None

def main():
    print("=" * 70)
    print("🚀 HCG Demo - Knowledge Base Setup (Managed Vector Store)")
    print("=" * 70 + "\n")
    
    results = {}
    
    for domain, config in KB_CONFIGS.items():
        print(f"{'=' * 70}")
        print(f"{domain.upper()} Knowledge Base")
        print(f"{'=' * 70}\n")
        
        count = upload_docs(domain, config)
        if count == 0:
            continue
        
        kb_id, kb_arn = create_kb_pinecone_style(domain, config)
        
        if kb_id:
            results[domain] = {
                'knowledge_base_id': kb_id,
                'knowledge_base_arn': kb_arn,
                'document_count': count,
                's3_prefix': config['s3_prefix']
            }
    
    with open('hcg_demo_knowledge_bases.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("=" * 70)
    print(f"✅ Created {len(results)} Knowledge Bases")
    print("=" * 70 + "\n")
    
    for domain, r in results.items():
        print(f"{domain.upper()}: {r['knowledge_base_id']}")

if __name__ == '__main__':
    main()
