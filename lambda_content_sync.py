import json
import boto3
from datetime import datetime
from urllib import request, parse

s3 = boto3.client('s3', region_name='ap-southeast-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')
ssm = boto3.client('ssm', region_name='ap-southeast-1')

owners_table = dynamodb.Table('hcg-demo-document-owners')
governance_table = dynamodb.Table('hcg-demo-content-governance')

# Content source configurations
SOURCES = {
    'sharepoint': {
        'url': 'https://company.sharepoint.com/sites/HCG',
        'auth_param': '/hcg-demo/sharepoint-token'
    },
    'confluence': {
        'url': 'https://company.atlassian.net/wiki',
        'auth_param': '/hcg-demo/confluence-token'
    }
}

# Document owners by domain
DOMAIN_OWNERS = {
    'hr': {'owner': 'hr-team@company.com', 'approver': 'hr-director@company.com'},
    'it': {'owner': 'it-team@company.com', 'approver': 'it-director@company.com'},
    'finance': {'owner': 'finance-team@company.com', 'approver': 'cfo@company.com'},
    'general': {'owner': 'admin-team@company.com', 'approver': 'admin-director@company.com'}
}

def lambda_handler(event, context):
    source = event.get('source', 'sharepoint')
    domain = event.get('domain', 'all')
    
    if source not in SOURCES:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid source'})}
    
    results = []
    domains = [domain] if domain != 'all' else DOMAIN_OWNERS.keys()
    
    for d in domains:
        synced = sync_domain_content(source, d)
        results.append({'domain': d, 'synced': synced})
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Sync completed',
            'source': source,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    }

def sync_domain_content(source, domain):
    # Get auth token from SSM
    token = get_auth_token(source)
    
    # Fetch documents from source
    documents = fetch_documents(source, domain, token)
    
    synced_count = 0
    for doc in documents:
        # Check if document is approved (GREEN zone)
        if is_approved(doc['id']):
            # Upload to S3
            s3_key = f"{domain}/{doc['id']}.txt"
            s3.put_object(
                Bucket='hcg-demo-knowledge-base',
                Key=s3_key,
                Body=doc['content'],
                Metadata={
                    'source': source,
                    'domain': domain,
                    'title': doc['title'],
                    'last_modified': doc['modified'],
                    'owner': DOMAIN_OWNERS[domain]['owner']
                }
            )
            
            # Assign owner
            assign_owner(doc['id'], domain)
            
            synced_count += 1
    
    # Trigger KB ingestion
    if synced_count > 0:
        trigger_ingestion(domain)
    
    return synced_count

def get_auth_token(source):
    try:
        response = ssm.get_parameter(
            Name=SOURCES[source]['auth_param'],
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except:
        return 'mock-token-for-demo'

def fetch_documents(source, domain, token):
    # Mock implementation - replace with actual API calls
    return [
        {
            'id': f'{domain}-policy-001',
            'title': f'{domain.upper()} Policy Document',
            'content': f'This is a {domain} policy document from {source}.',
            'modified': datetime.now().isoformat()
        }
    ]

def is_approved(doc_id):
    try:
        response = governance_table.query(
            KeyConditionExpression='document_id = :doc_id',
            ExpressionAttributeValues={':doc_id': doc_id},
            ScanIndexForward=False,
            Limit=1
        )
        if response['Items']:
            return response['Items'][0]['zone'] == 'GREEN'
        return False  # Not approved yet
    except:
        return False

def assign_owner(doc_id, domain):
    owners_table.put_item(Item={
        'domain': domain,
        'document_id': doc_id,
        'owner': DOMAIN_OWNERS[domain]['owner'],
        'approver': DOMAIN_OWNERS[domain]['approver'],
        'assigned_at': datetime.now().isoformat()
    })

def trigger_ingestion(domain):
    kb_map = {
        'hr': 'H0LFPBHIAK',
        'it': 'X1VW7AMIK8',
        'finance': '1MFT5GZYTT',
        'general': 'BOLGBDCUAZ'
    }
    kb_id = kb_map.get(domain)
    if kb_id:
        try:
            bedrock_agent.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=f'hcg-demo-kb-{domain}'
            )
        except:
            pass
