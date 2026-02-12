import json
import boto3

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
catalog_table = dynamodb.Table('hcg-demo-resource-catalog')

# Redirectional query patterns (65% of volume per PRD)
REDIRECTIONAL_PATTERNS = [
    'where', 'how do i', 'link to', 'access', 'portal', 'system',
    'submit', 'create', 'request', 'apply', 'enroll', 'view'
]

def is_redirectional_query(query):
    query_lower = query.lower()
    return any(pattern in query_lower for pattern in REDIRECTIONAL_PATTERNS)

def handle_redirectional_query(query, domain, user_email):
    # Invoke deep linking Lambda
    response = lambda_client.invoke(
        FunctionName='hcg-demo-deep-linking',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'generate_link',
            'query': query,
            'domain': domain,
            'user_email': user_email
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        return {
            'type': 'redirect',
            'resource': body['resource_name'],
            'link': body['link'],
            'sso_enabled': body['sso_enabled'],
            'description': body['description'],
            'contact': body.get('contact')
        }
    else:
        return None

def format_redirect_response(redirect_info):
    response = f"🔗 **{redirect_info['description']}**\n\n"
    
    if redirect_info['sso_enabled']:
        response += f"Click here to access via SSO: {redirect_info['link']}\n"
        response += "✅ Single Sign-On enabled - you'll be logged in automatically\n"
    else:
        response += f"Access link: {redirect_info['link']}\n"
        response += "⚠️ You may need to log in manually\n"
    
    if redirect_info.get('contact'):
        response += f"\n📧 Need help? Contact: {redirect_info['contact']}"
    
    return response

# Example integration in supervisor agent
def enhanced_supervisor_handler(event, context):
    query = event.get('query')
    domain = event.get('domain')
    user_email = event.get('user_email')
    
    # Check if redirectional query
    if is_redirectional_query(query):
        redirect_info = handle_redirectional_query(query, domain, user_email)
        
        if redirect_info:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'response_type': 'redirect',
                    'message': format_redirect_response(redirect_info),
                    'redirect_info': redirect_info
                })
            }
    
    # Otherwise, route to specialist agent (existing logic)
    return route_to_specialist_agent(query, domain)

def route_to_specialist_agent(query, domain):
    # Existing supervisor logic
    pass
