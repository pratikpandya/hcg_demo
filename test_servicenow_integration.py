import boto3
import json
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

print("="*70)
print("SERVICENOW INTEGRATION TEST")
print("="*70)

# Test 1: Create Incident
print("\nTest 1: Create ServiceNow Incident")
print("-" * 70)

payload = {
    'actionGroup': 'ServiceNowActions',
    'apiPath': '/create_incident',
    'httpMethod': 'POST',
    'parameters': [
        {'name': 'short_description', 'value': 'Test incident - VPN connection issue'},
        {'name': 'description', 'value': 'User reported VPN not working. This is a test incident.'},
        {'name': 'category', 'value': 'Network'},
        {'name': 'urgency', 'value': '2'}
    ],
    'requestBody': {
        'content': {
            'application/json': {
                'properties': [
                    {'name': 'user_email', 'value': 'test.user@company.com'}
                ]
            }
        }
    }
}

try:
    response = lambda_client.invoke(
        FunctionName='hcg-demo-servicenow-action',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    print(f"Status Code: {response['StatusCode']}")
    
    if result.get('response', {}).get('httpStatusCode') == 200:
        body = json.loads(result['response']['responseBody']['application/json']['body'])
        
        print("\n✅ Incident created successfully!")
        print(f"\nIncident Details:")
        print(f"  Number: {body.get('incident_number')}")
        print(f"  Sys ID: {body.get('sys_id')}")
        print(f"  Priority: {body.get('priority')}")
        print(f"  Link: {body.get('link')}")
        
        incident_number = body.get('incident_number')
        
        # Test 2: Get Incident Status
        print(f"\n{'='*70}")
        print("Test 2: Get Incident Status")
        print("-" * 70)
        
        status_payload = {
            'actionGroup': 'ServiceNowActions',
            'apiPath': '/get_incident_status',
            'httpMethod': 'GET',
            'parameters': [
                {'name': 'incident_number', 'value': incident_number}
            ]
        }
        
        status_response = lambda_client.invoke(
            FunctionName='hcg-demo-servicenow-action',
            InvocationType='RequestResponse',
            Payload=json.dumps(status_payload)
        )
        
        status_result = json.loads(status_response['Payload'].read())
        
        if status_result.get('response', {}).get('httpStatusCode') == 200:
            status_body = json.loads(status_result['response']['responseBody']['application/json']['body'])
            
            print("\n✅ Status retrieved successfully!")
            print(f"\nIncident Status:")
            print(f"  Number: {status_body.get('incident_number')}")
            print(f"  State: {status_body.get('state')}")
            print(f"  Priority: {status_body.get('priority')}")
            print(f"  Description: {status_body.get('short_description')}")
        else:
            print(f"\n❌ Failed to get status")
            print(f"Response: {status_result}")
    
    else:
        error_body = result['response']['responseBody']['application/json']['body']
        print(f"\n❌ Failed to create incident")
        print(f"Error: {error_body}")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")

print(f"\n{'='*70}")
print("TEST COMPLETE")
print("="*70)
