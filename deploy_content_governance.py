import boto3
import json
import zipfile
import io
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
iam = boto3.client('iam', region_name='ap-southeast-1')

def create_lambda_role():
    role_name = 'hcg-demo-content-governance-role'
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for HCG Demo content governance Lambda functions'
        )
        role_arn = response['Role']['Arn']
        print(f"✅ Created IAM role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        response = iam.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"✅ Using existing IAM role: {role_name}")
    
    # Attach policies
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
        'arn:aws:iam::aws:policy/AmazonS3FullAccess',
        'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
        'arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess'
    ]
    
    for policy in policies:
        try:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy)
        except:
            pass
    
    return role_arn

def create_lambda_function(name, code_file, role_arn):
    # Create deployment package
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        with open(code_file, 'r') as f:
            zip_file.writestr('lambda_function.py', f.read())
    
    zip_buffer.seek(0)
    
    try:
        response = lambda_client.create_function(
            FunctionName=name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_buffer.read()},
            Timeout=60,
            MemorySize=256,
            Environment={'Variables': {'REGION': 'ap-southeast-1'}}
        )
        print(f"✅ Created Lambda function: {name}")
        return response['FunctionArn']
    except lambda_client.exceptions.ResourceConflictException:
        # Update existing function
        zip_buffer.seek(0)
        lambda_client.update_function_code(
            FunctionName=name,
            ZipFile=zip_buffer.read()
        )
        print(f"✅ Updated Lambda function: {name}")
        response = lambda_client.get_function(FunctionName=name)
        return response['Configuration']['FunctionArn']

if __name__ == '__main__':
    print("Deploying Content Governance components...\n")
    
    # Step 1: Create DynamoDB tables
    print("Step 1: Creating DynamoDB tables...")
    import subprocess
    subprocess.run(['python', 'content_governance_schema.py'], check=True)
    
    # Step 2: Create IAM role
    print("\nStep 2: Creating IAM role...")
    role_arn = create_lambda_role()
    
    # Wait for role propagation
    print("Waiting for IAM role propagation...")
    import time
    time.sleep(10)
    
    # Step 3: Create Lambda functions
    print("\nStep 3: Creating Lambda functions...")
    governance_arn = create_lambda_function(
        'hcg-demo-content-governance',
        'lambda_content_governance.py',
        role_arn
    )
    
    sync_arn = create_lambda_function(
        'hcg-demo-content-sync',
        'lambda_content_sync.py',
        role_arn
    )
    
    # Step 4: Create EventBridge schedules
    print("\nStep 4: Creating EventBridge schedules...")
    subprocess.run(['python', 'create_sync_schedules.py'], check=True)
    
    # Step 5: Initialize governance data
    print("\nStep 5: Initializing governance data...")
    subprocess.run(['python', 'initialize_governance.py'], check=True)
    
    # Save resource IDs
    resources = {
        'governance_lambda_arn': governance_arn,
        'sync_lambda_arn': sync_arn,
        'iam_role_arn': role_arn,
        'deployed_at': datetime.now().isoformat()
    }
    
    with open('content_governance_resources.json', 'w') as f:
        json.dump(resources, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ Content Governance deployment completed successfully!")
    print("="*60)
    print(f"\nResources created:")
    print(f"  - DynamoDB tables: 2")
    print(f"  - Lambda functions: 2")
    print(f"  - EventBridge rules: 3")
    print(f"  - Documents initialized: 10")
    print(f"\nSchedules:")
    print(f"  - Daily sync: 2 AM SGT")
    print(f"  - Quarterly review: 1st of quarter at 10 AM SGT")
    print(f"  - Weekly review check: Every Monday at 9 AM SGT")
