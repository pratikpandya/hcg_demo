import boto3
import json
import getpass

ssm = boto3.client('ssm', region_name='ap-southeast-1')

print("="*70)
print("SERVICENOW INSTANCE CONFIGURATION")
print("="*70)

# Use provided instance
instance_url = "https://dev355778.service-now.com"

print(f"\nServiceNow Instance: {instance_url}")
print("\nPlease provide credentials:")

username = input("Username: ").strip()
password = getpass.getpass("Password: ")

if not username or not password:
    print("\n❌ Error: Username and Password are required!")
    exit(1)

print("\n" + "="*70)
print("Storing credentials in AWS Systems Manager Parameter Store...")
print("="*70)

try:
    # Store instance URL
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/instance-url',
        Value=instance_url,
        Type='String',
        Overwrite=True,
        Description='ServiceNow instance URL'
    )
    print("✅ Stored: /hcg-demo/servicenow/instance-url")
    
    # Store username
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/username',
        Value=username,
        Type='String',
        Overwrite=True,
        Description='ServiceNow username'
    )
    print("✅ Stored: /hcg-demo/servicenow/username")
    
    # Store password (encrypted)
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/password',
        Value=password,
        Type='SecureString',
        Overwrite=True,
        Description='ServiceNow password (encrypted)'
    )
    print("✅ Stored: /hcg-demo/servicenow/password (encrypted)")
    
    # Save configuration summary
    config = {
        'instance_url': instance_url,
        'username': username,
        'auth_type': 'basic',
        'configured_at': '2025-02-12',
        'parameters': {
            'instance_url': '/hcg-demo/servicenow/instance-url',
            'username': '/hcg-demo/servicenow/username',
            'password': '/hcg-demo/servicenow/password'
        }
    }
    
    with open('servicenow_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Configuration saved to servicenow_config.json")
    
    print("\n" + "="*70)
    print("✅ ServiceNow credentials configured successfully!")
    print("="*70)
    print("\nNext step: Update Lambda function")
    print("Run: python update_servicenow_lambda.py")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    exit(1)
