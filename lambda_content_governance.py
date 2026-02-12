import json
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
s3 = boto3.client('s3', region_name='ap-southeast-1')
bedrock_agent = boto3.client('bedrock-agent', region_name='ap-southeast-1')

governance_table = dynamodb.Table('hcg-demo-content-governance')
owners_table = dynamodb.Table('hcg-demo-document-owners')

# Zone definitions
ZONES = {
    'GREEN': {'description': 'Approved policies only', 'auto_publish': True, 'review_days': 90},
    'YELLOW': {'description': 'Pending review', 'auto_publish': False, 'review_days': 30},
    'RED': {'description': 'Rejected/Outdated', 'auto_publish': False, 'review_days': 0}
}

def lambda_handler(event, context):
    action = event.get('action')
    
    if action == 'approve_document':
        return approve_document(event)
    elif action == 'review_document':
        return review_document(event)
    elif action == 'check_zone':
        return check_zone(event)
    elif action == 'get_pending_reviews':
        return get_pending_reviews(event)
    else:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid action'})}

def approve_document(event):
    doc_id = event['document_id']
    domain = event['domain']
    approver = event['approver']
    zone = event.get('zone', 'YELLOW')
    
    if zone not in ZONES:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid zone'})}
    
    version = int(datetime.now().timestamp())
    review_date = (datetime.now() + timedelta(days=ZONES[zone]['review_days'])).isoformat()
    
    # Store governance record
    governance_table.put_item(Item={
        'document_id': doc_id,
        'version': version,
        'domain': domain,
        'zone': zone,
        'approver': approver,
        'approved_at': datetime.now().isoformat(),
        'review_date': review_date,
        'status': 'APPROVED' if zone == 'GREEN' else 'PENDING'
    })
    
    # Auto-publish GREEN zone documents
    if zone == 'GREEN' and ZONES[zone]['auto_publish']:
        sync_to_kb(doc_id, domain)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Document approved in {zone} zone',
            'document_id': doc_id,
            'zone': zone,
            'review_date': review_date,
            'auto_published': zone == 'GREEN'
        })
    }

def review_document(event):
    doc_id = event['document_id']
    reviewer = event['reviewer']
    new_zone = event.get('new_zone')
    comments = event.get('comments', '')
    
    # Get current version
    response = governance_table.query(
        KeyConditionExpression='document_id = :doc_id',
        ExpressionAttributeValues={':doc_id': doc_id},
        ScanIndexForward=False,
        Limit=1
    )
    
    if not response['Items']:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Document not found'})}
    
    current = response['Items'][0]
    version = int(datetime.now().timestamp())
    
    # Update zone if provided
    zone = new_zone if new_zone else current['zone']
    review_date = (datetime.now() + timedelta(days=ZONES[zone]['review_days'])).isoformat()
    
    governance_table.put_item(Item={
        'document_id': doc_id,
        'version': version,
        'domain': current['domain'],
        'zone': zone,
        'reviewer': reviewer,
        'reviewed_at': datetime.now().isoformat(),
        'review_date': review_date,
        'comments': comments,
        'previous_zone': current['zone'],
        'status': 'REVIEWED'
    })
    
    # Remove from KB if moved to RED zone
    if zone == 'RED':
        remove_from_kb(doc_id, current['domain'])
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Document reviewed',
            'document_id': doc_id,
            'previous_zone': current['zone'],
            'new_zone': zone,
            'review_date': review_date
        })
    }

def check_zone(event):
    doc_id = event['document_id']
    
    response = governance_table.query(
        KeyConditionExpression='document_id = :doc_id',
        ExpressionAttributeValues={':doc_id': doc_id},
        ScanIndexForward=False,
        Limit=1
    )
    
    if not response['Items']:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Document not found'})}
    
    doc = response['Items'][0]
    return {
        'statusCode': 200,
        'body': json.dumps({
            'document_id': doc_id,
            'zone': doc['zone'],
            'review_date': doc['review_date'],
            'status': doc['status']
        })
    }

def get_pending_reviews(event):
    today = datetime.now().isoformat()
    
    response = governance_table.query(
        IndexName='review-date-index',
        KeyConditionExpression='review_date <= :today',
        ExpressionAttributeValues={':today': today}
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'pending_reviews': response['Items'],
            'count': len(response['Items'])
        })
    }

def sync_to_kb(doc_id, domain):
    kb_map = {
        'hr': 'H0LFPBHIAK',
        'it': 'X1VW7AMIK8',
        'finance': '1MFT5GZYTT',
        'general': 'BOLGBDCUAZ'
    }
    kb_id = kb_map.get(domain.lower())
    if kb_id:
        bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=f'hcg-demo-kb-{domain.lower()}'
        )

def remove_from_kb(doc_id, domain):
    # Mark as deleted in S3 metadata
    s3.put_object_tagging(
        Bucket='hcg-demo-knowledge-base',
        Key=f'{domain.lower()}/{doc_id}',
        Tagging={'TagSet': [{'Key': 'status', 'Value': 'deleted'}]}
    )
