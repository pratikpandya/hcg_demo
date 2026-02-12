import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
catalog_table = dynamodb.Table('hcg-demo-resource-catalog')

def lambda_handler(event, context):
    action = event.get('action', 'generate_link')
    
    if action == 'generate_link':
        return generate_deep_link(event)
    elif action == 'search_resources':
        return search_resources(event)
    elif action == 'get_resource':
        return get_resource(event)
    else:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid action'})}

def generate_deep_link(event):
    query = event.get('query', '').lower()
    user_email = event.get('user_email')
    domain = event.get('domain')
    
    # Find matching resource
    resource = find_resource_by_query(query, domain)
    
    if not resource:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'No matching resource found', 'query': query})
        }
    
    # Generate SSO-enabled deep link
    deep_link = build_deep_link(resource, query, user_email)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'resource_name': resource['name'],
            'resource_id': resource['resource_id'],
            'link': deep_link['url'],
            'sso_enabled': resource['sso_enabled'],
            'description': deep_link['description'],
            'category': resource['category'],
            'contact': resource.get('contact')
        })
    }

def find_resource_by_query(query, domain=None):
    # Scan catalog for keyword matches
    if domain:
        response = catalog_table.query(
            IndexName='domain-index',
            KeyConditionExpression='#d = :domain',
            ExpressionAttributeNames={'#d': 'domain'},
            ExpressionAttributeValues={':domain': domain}
        )
        resources = response['Items']
    else:
        response = catalog_table.scan()
        resources = response['Items']
    
    # Score resources by keyword match
    scored = []
    for resource in resources:
        score = 0
        for keyword in resource.get('keywords', []):
            if keyword in query:
                score += 1
        if score > 0:
            scored.append((score, resource))
    
    if scored:
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[0][1]
    
    return None

def build_deep_link(resource, query, user_email):
    base_url = resource['base_url']
    deep_links = resource.get('deep_links', {})
    
    # Match query to specific deep link
    link_path = '/'
    description = f"Access {resource['name']}"
    
    for link_name, path in deep_links.items():
        if link_name.replace('_', ' ') in query:
            link_path = path
            description = f"{link_name.replace('_', ' ').title()} in {resource['name']}"
            break
    
    # Build SSO-enabled URL
    if resource['sso_enabled']:
        sso_provider = resource.get('sso_provider', 'okta')
        if sso_provider == 'okta':
            url = f"https://company.okta.com/home/bookmark/0oa{resource['resource_id']}/2557?fromHome=true"
        elif sso_provider == 'azure_ad':
            url = f"https://myapps.microsoft.com/signin/{resource['resource_id']}"
        else:
            url = f"{base_url}{link_path}"
    else:
        url = f"{base_url}{link_path}"
    
    return {
        'url': url,
        'description': description,
        'requires_sso': resource['sso_enabled']
    }

def search_resources(event):
    category = event.get('category')
    domain = event.get('domain')
    
    if category:
        response = catalog_table.query(
            IndexName='category-index',
            KeyConditionExpression='category = :category',
            ExpressionAttributeValues={':category': category}
        )
    elif domain:
        response = catalog_table.query(
            IndexName='domain-index',
            KeyConditionExpression='#d = :domain',
            ExpressionAttributeNames={'#d': 'domain'},
            ExpressionAttributeValues={':domain': domain}
        )
    else:
        response = catalog_table.scan()
    
    resources = [{
        'resource_id': r['resource_id'],
        'name': r['name'],
        'category': r['category'],
        'domain': r['domain'],
        'base_url': r['base_url'],
        'sso_enabled': r['sso_enabled']
    } for r in response['Items']]
    
    return {
        'statusCode': 200,
        'body': json.dumps({'resources': resources, 'count': len(resources)})
    }

def get_resource(event):
    resource_id = event.get('resource_id')
    
    response = catalog_table.get_item(Key={'resource_id': resource_id})
    
    if 'Item' not in response:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Resource not found'})}
    
    return {
        'statusCode': 200,
        'body': json.dumps({'resource': response['Item']})
    }
