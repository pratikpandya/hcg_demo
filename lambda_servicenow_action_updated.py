import json
import boto3
from urllib import request, parse, error
from datetime import datetime, timedelta
import base64
import ssl

# Create SSL context that doesn't verify certificates (for dev instances)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

ssm = boto3.client('ssm', region_name='ap-southeast-1')

# Cache for credentials (valid for Lambda execution context)
_credentials_cache = {}
_cache_expiry = None

def get_servicenow_credentials():
    """Retrieve ServiceNow credentials from Parameter Store with caching"""
    global _credentials_cache, _cache_expiry
    
    # Check cache
    if _credentials_cache and _cache_expiry and datetime.now() < _cache_expiry:
        return _credentials_cache
    
    try:
        # Get parameters
        response = ssm.get_parameters(
            Names=[
                '/hcg-demo/servicenow/instance-url',
                '/hcg-demo/servicenow/username',
                '/hcg-demo/servicenow/password'
            ],
            WithDecryption=True
        )
        
        params = {p['Name'].split('/')[-1]: p['Value'] for p in response['Parameters']}
        
        _credentials_cache = {
            'instance_url': params.get('instance-url'),
            'username': params.get('username'),
            'password': params.get('password')
        }
        
        # Cache for 5 minutes
        _cache_expiry = datetime.now() + timedelta(minutes=5)
        
        return _credentials_cache
    
    except Exception as e:
        print(f"Error retrieving credentials: {str(e)}")
        return None

def create_incident(short_description, description, category='General', urgency='3', user_email=None):
    """Create ServiceNow incident"""
    creds = get_servicenow_credentials()
    
    if not creds:
        return {
            'success': False,
            'error': 'ServiceNow credentials not configured'
        }
    
    url = f"{creds['instance_url']}/api/now/table/incident"
    
    # Prepare incident data
    data = {
        'short_description': short_description,
        'description': description,
        'category': category,
        'urgency': urgency,
        'impact': '2',
        'state': '1'  # New
    }
    
    if user_email:
        data['caller_id'] = user_email
    
    # Create request
    req = request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode(
                f"{creds['username']}:{creds['password']}".encode()
            ).decode()
        },
        method='POST'
    )
    
    try:
        with request.urlopen(req, timeout=10, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            incident = result.get('result', {})
            
            return {
                'success': True,
                'incident_number': incident.get('number'),
                'sys_id': incident.get('sys_id'),
                'state': incident.get('state'),
                'priority': incident.get('priority'),
                'link': f"{creds['instance_url']}/nav_to.do?uri=incident.do?sys_id={incident.get('sys_id')}"
            }
    
    except error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {
            'success': False,
            'error': f'HTTP {e.code}: {error_body}'
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_incident_status(incident_number):
    """Get incident status"""
    creds = get_servicenow_credentials()
    
    if not creds:
        return {
            'success': False,
            'error': 'ServiceNow credentials not configured'
        }
    
    url = f"{creds['instance_url']}/api/now/table/incident?sysparm_query=number={incident_number}"
    
    req = request.Request(
        url,
        headers={
            'Accept': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode(
                f"{creds['username']}:{creds['password']}".encode()
            ).decode()
        }
    )
    
    try:
        with request.urlopen(req, timeout=10, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            incidents = result.get('result', [])
            
            if not incidents:
                return {
                    'success': False,
                    'error': 'Incident not found'
                }
            
            incident = incidents[0]
            return {
                'success': True,
                'incident_number': incident.get('number'),
                'state': incident.get('state'),
                'priority': incident.get('priority'),
                'assigned_to': incident.get('assigned_to'),
                'short_description': incident.get('short_description')
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def lambda_handler(event, context):
    """Main Lambda handler for Bedrock Agent Action Group"""
    
    # Extract action details
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    
    # Extract parameters
    parameters = event.get('parameters', [])
    params = {p['name']: p['value'] for p in parameters}
    
    # Extract request body
    request_body = event.get('requestBody', {})
    body_props = request_body.get('content', {}).get('application/json', {}).get('properties', [])
    body_params = {p['name']: p['value'] for p in body_props}
    
    # Merge parameters
    all_params = {**params, **body_params}
    
    # Route to appropriate action
    if api_path == '/create_incident':
        result = create_incident(
            short_description=all_params.get('short_description', 'Support request'),
            description=all_params.get('description', ''),
            category=all_params.get('category', 'General'),
            urgency=all_params.get('urgency', '3'),
            user_email=all_params.get('user_email')
        )
    
    elif api_path == '/get_incident_status':
        result = get_incident_status(
            incident_number=all_params.get('incident_number')
        )
    
    else:
        result = {
            'success': False,
            'error': f'Unknown action: {api_path}'
        }
    
    # Format response for Bedrock Agent
    if result.get('success'):
        response_body = json.dumps(result)
        status_code = 200
    else:
        response_body = json.dumps({'error': result.get('error')})
        status_code = 500
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': response_body
                }
            }
        }
    }
