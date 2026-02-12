import boto3
import json

ssm = boto3.client('ssm', region_name='ap-southeast-1')

print("="*70)
print("SERVICENOW INSTANCE CONFIGURATION")
print("="*70)

# Collect ServiceNow instance details
print("\nPlease provide your ServiceNow instance details:")
print("(These will be securely stored in AWS Systems Manager Parameter Store)\n")

instance_url = input("ServiceNow Instance URL (e.g., https://dev12345.service-now.com): ").strip()
username = input("ServiceNow Username (e.g., admin): ").strip()
password = input("ServiceNow Password: ").strip()
client_id = input("OAuth Client ID (optional, press Enter to skip): ").strip()
client_secret = input("OAuth Client Secret (optional, press Enter to skip): ").strip()

# Validate inputs
if not instance_url or not username or not password:
    print("\n❌ Error: Instance URL, Username, and Password are required!")
    exit(1)

# Remove trailing slash from URL
instance_url = instance_url.rstrip('/')

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
    
    # Store OAuth credentials if provided
    if client_id and client_secret:
        ssm.put_parameter(
            Name='/hcg-demo/servicenow/client-id',
            Value=client_id,
            Type='String',
            Overwrite=True,
            Description='ServiceNow OAuth client ID'
        )
        print("✅ Stored: /hcg-demo/servicenow/client-id")
        
        ssm.put_parameter(
            Name='/hcg-demo/servicenow/client-secret',
            Value=client_secret,
            Type='SecureString',
            Overwrite=True,
            Description='ServiceNow OAuth client secret (encrypted)'
        )
        print("✅ Stored: /hcg-demo/servicenow/client-secret (encrypted)")
    
    # Save configuration summary
    config = {
        'instance_url': instance_url,
        'username': username,
        'auth_type': 'oauth' if client_id else 'basic',
        'parameters': {
            'instance_url': '/hcg-demo/servicenow/instance-url',
            'username': '/hcg-demo/servicenow/username',
            'password': '/hcg-demo/servicenow/password'
        }
    }
    
    if client_id:
        config['parameters']['client_id'] = '/hcg-demo/servicenow/client-id'
        config['parameters']['client_secret'] = '/hcg-demo/servicenow/client-secret'
    
    with open('servicenow_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Configuration saved to servicenow_config.json")
    
    print("\n" + "="*70)
    print("✅ ServiceNow credentials configured successfully!")
    print("="*70)
    print("\nNext steps:")
    print("1. Update Lambda function with new configuration")
    print("2. Test ServiceNow integration")
    print("\nRun: python update_servicenow_lambda.py")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    exit(1)
