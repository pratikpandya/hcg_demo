import json
import boto3
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

secrets_client = boto3.client('secretsmanager', region_name='ap-southeast-1')

# Cache for OAuth token
token_cache = {'token': None, 'expires_at': None}

def get_servicenow_credentials():
    """Retrieve ServiceNow credentials from Secrets Manager"""
    response = secrets_client.get_secret_value(SecretId='hcg-demo/servicenow/oauth')
    secret = json.loads(response['SecretString'])
    return secret

def get_oauth_token():
    """Get OAuth token with caching"""
    now = datetime.now()
    
    if token_cache['token'] and token_cache['expires_at'] and now < token_cache['expires_at']:
        return token_cache['token']
    
    creds = get_servicenow_credentials()
    
    token_url = f"https://{creds['instance']}.service-now.com/oauth_token.do"
    
    data = urllib.parse.urlencode({
        'grant_type': 'password',
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'username': creds['username'],
        'password': creds['password']
    }).encode()
    
    req = urllib.request.Request(token_url, data=data, method='POST')
    
    with urllib.request.urlopen(req) as response:
        token_data = json.loads(response.read().decode())
    
    token_cache['token'] = token_data['access_token']
    token_cache['expires_at'] = now + timedelta(seconds=token_data.get('expires_in', 3600) - 60)
    
    return token_cache['token']

def create_incident(short_description, description, caller_id='admin', urgency='3', impact='3'):
    """Create ServiceNow incident"""
    creds = get_servicenow_credentials()
    token = get_oauth_token()
    
    url = f"https://{creds['instance']}.service-now.com/api/now/table/incident"
    
    payload = {
        'short_description': short_description,
        'description': description,
        'caller_id': caller_id,
        'urgency': urgency,
        'impact': impact,
        'category': 'inquiry',
        'assignment_group': 'IT Support'
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserToken': caller_id
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())['result']
    
    return {
        'incident_number': result['number'],
        'sys_id': result['sys_id'],
        'state': result['state'],
        'short_description': result['short_description']
    }

def get_incident_status(incident_number):
    """Get incident status"""
    creds = get_servicenow_credentials()
    token = get_oauth_token()
    
    params = urllib.parse.urlencode({
        'sysparm_query': f'number={incident_number}',
        'sysparm_fields': 'number,state,short_description,sys_updated_on'
    })
    
    url = f"https://{creds['instance']}.service-now.com/api/now/table/incident?{params}"
    
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
    )
    
    with urllib.request.urlopen(req) as response:
        results = json.loads(response.read().decode())['result']
    
    if not results:
        return {'error': 'Incident not found'}
    
    incident = results[0]
    
    state_map = {
        '1': 'New',
        '2': 'In Progress',
        '3': 'On Hold',
        '6': 'Resolved',
        '7': 'Closed'
    }
    
    return {
        'incident_number': incident['number'],
        'state': state_map.get(incident['state'], 'Unknown'),
        'short_description': incident['short_description'],
        'last_updated': incident['sys_updated_on']
    }

def lambda_handler(event, context):
    """ServiceNow Action Group handler"""
    
    try:
        # Parse Bedrock agent event
        action = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters to dict
        params = {p['name']: p['value'] for p in parameters}
        
        # Route to appropriate function
        if api_path == '/create_incident':
            result = create_incident(
                short_description=params.get('short_description', 'IT Support Request'),
                description=params.get('description', ''),
                caller_id=params.get('caller_id', 'admin'),
                urgency=params.get('urgency', '3'),
                impact=params.get('impact', '3')
            )
            
            response_body = {
                'TEXT': {
                    'body': f"Incident created: {result['incident_number']}. Status: {result['state']}"
                }
            }
            
        elif api_path == '/get_incident_status':
            result = get_incident_status(
                incident_number=params.get('incident_number', '')
            )
            
            if 'error' in result:
                response_body = {
                    'TEXT': {
                        'body': result['error']
                    }
                }
            else:
                response_body = {
                    'TEXT': {
                        'body': f"Incident {result['incident_number']}: {result['state']}. Last updated: {result['last_updated']}"
                    }
                }
        
        else:
            response_body = {
                'TEXT': {
                    'body': f"Unknown action: {api_path}"
                }
            }
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'apiPath': api_path,
                'httpMethod': 'POST',
                'httpStatusCode': 200,
                'responseBody': response_body
            }
        }
        
    except Exception as e:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', ''),
                'apiPath': event.get('apiPath', ''),
                'httpMethod': 'POST',
                'httpStatusCode': 500,
                'responseBody': {
                    'TEXT': {
                        'body': f"Error: {str(e)}"
                    }
                }
            }
        }
