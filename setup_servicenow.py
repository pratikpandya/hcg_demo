import boto3
import json

ssm = boto3.client('ssm', region_name='ap-southeast-1')

print("="*70)
print("SERVICENOW INSTANCE CONFIGURATION")
print("="*70)

instance_url = "https://dev355778.service-now.com"
username = "Panpratik07@gmail.com"
password = "rpt9uJ3!UKVf7zJ"

print(f"\nInstance: {instance_url}")
print(f"Username: {username}")
print("\nStoring credentials in AWS Systems Manager Parameter Store...")

try:
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/instance-url',
        Value=instance_url,
        Type='String',
        Overwrite=True
    )
    print("✅ Stored: instance-url")
    
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/username',
        Value=username,
        Type='String',
        Overwrite=True
    )
    print("✅ Stored: username")
    
    ssm.put_parameter(
        Name='/hcg-demo/servicenow/password',
        Value=password,
        Type='SecureString',
        Overwrite=True
    )
    print("✅ Stored: password (encrypted)")
    
    with open('servicenow_config.json', 'w') as f:
        json.dump({
            'instance_url': instance_url,
            'username': username,
            'configured_at': '2025-02-12'
        }, f, indent=2)
    
    print("\n✅ Configuration complete!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    exit(1)
