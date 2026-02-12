import boto3
import json
from urllib import request
import base64

ssm = boto3.client('ssm', region_name='ap-southeast-1')

# Get credentials
response = ssm.get_parameters(
    Names=[
        '/hcg-demo/servicenow/instance-url',
        '/hcg-demo/servicenow/username',
        '/hcg-demo/servicenow/password'
    ],
    WithDecryption=True
)

params = {p['Name'].split('/')[-1]: p['Value'] for p in response['Parameters']}

instance_url = params['instance-url']
username = params['username']
password = params['password']

print(f"Instance: {instance_url}")
print(f"Username: {username}")
print("\nTesting ServiceNow API...")

# Create incident
url = f"{instance_url}/api/now/table/incident"
data = {
    'short_description': 'Test incident from HCG Demo',
    'description': 'Testing ServiceNow integration',
    'category': 'Network',
    'urgency': '2'
}

req = request.Request(
    url,
    data=json.dumps(data).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + base64.b64encode(f"{username}:{password}".encode()).decode()
    },
    method='POST'
)

try:
    with request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        incident = result.get('result', {})
        
        print(f"\n✅ Incident created successfully!")
        print(f"  Number: {incident.get('number')}")
        print(f"  Sys ID: {incident.get('sys_id')}")
        print(f"  Link: {instance_url}/nav_to.do?uri=incident.do?sys_id={incident.get('sys_id')}")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
