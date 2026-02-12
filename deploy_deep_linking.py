import boto3
import json
import zipfile
import io
import time
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
events = boto3.client('events', region_name='ap-southeast-1')
iam = boto3.client('iam', region_name='ap-southeast-1')

def create_lambda_role():
    role_name = 'hcg-demo-deep-linking-role'
    
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
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = response['Role']['Arn']
        print(f"✅ Created IAM role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        response = iam.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"✅ Using existing IAM role: {role_name}")
    
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
        'arn:aws:iam::aws:policy/CloudWatchFullAccess'
    ]
    
    for policy in policies:
        try:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy)
        except:
            pass
    
    return role_arn

def create_lambda_function(name, code_file, role_arn):
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
            Timeout=30,
            MemorySize=256
        )
        print(f"✅ Created Lambda function: {name}")
        return response['FunctionArn']
    except lambda_client.exceptions.ResourceConflictException:
        zip_buffer.seek(0)
        lambda_client.update_function_code(FunctionName=name, ZipFile=zip_buffer.read())
        print(f"✅ Updated Lambda function: {name}")
        response = lambda_client.get_function(FunctionName=name)
        return response['Configuration']['FunctionArn']

def create_health_check_schedule():
    rule_name = 'hcg-demo-link-health-check'
    
    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression='rate(1 hour)',
        State='ENABLED',
        Description='Hourly link health check for deep linking resources'
    )
    
    events.put_targets(
        Rule=rule_name,
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:ap-southeast-1:026138522123:function:hcg-demo-link-health-check'
        }]
    )
    
    try:
        lambda_client.add_permission(
            FunctionName='hcg-demo-link-health-check',
            StatementId='EventBridge-health-check',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com'
        )
    except:
        pass
    
    print(f"✅ Created EventBridge rule: {rule_name} (hourly)")

if __name__ == '__main__':
    print("Deploying Deep Linking Infrastructure...\n")
    
    # Step 1: Create DynamoDB tables
    print("Step 1: Creating DynamoDB tables...")
    import subprocess
    subprocess.run(['python', 'deep_linking_schema.py'], check=True)
    
    print("Waiting for DynamoDB tables to be ready...")
    time.sleep(15)
    
    # Step 2: Populate resource catalog
    print("\nStep 2: Populating resource catalog...")
    subprocess.run(['python', 'populate_resource_catalog.py'], check=True)
    
    # Step 3: Create IAM role
    print("\nStep 3: Creating IAM role...")
    role_arn = create_lambda_role()
    print("Waiting for IAM role propagation...")
    time.sleep(10)
    
    # Step 4: Create Lambda functions
    print("\nStep 4: Creating Lambda functions...")
    deep_linking_arn = create_lambda_function(
        'hcg-demo-deep-linking',
        'lambda_deep_linking.py',
        role_arn
    )
    
    health_check_arn = create_lambda_function(
        'hcg-demo-link-health-check',
        'lambda_link_health_check.py',
        role_arn
    )
    
    # Step 5: Create health check schedule
    print("\nStep 5: Creating health check schedule...")
    create_health_check_schedule()
    
    # Save resource IDs
    resources = {
        'deep_linking_lambda_arn': deep_linking_arn,
        'health_check_lambda_arn': health_check_arn,
        'iam_role_arn': role_arn,
        'deployed_at': datetime.now().isoformat()
    }
    
    with open('deep_linking_resources.json', 'w') as f:
        json.dump(resources, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ Deep Linking Infrastructure deployment completed!")
    print("="*60)
    print(f"\nResources created:")
    print(f"  - DynamoDB tables: 2")
    print(f"  - Lambda functions: 2")
    print(f"  - EventBridge rules: 1")
    print(f"  - Resource catalog: 10 systems/portals")
    print(f"\nCapabilities:")
    print(f"  - SSO-enabled deep links")
    print(f"  - Hourly link health checks")
    print(f"  - Redirectional query handling (65% of volume)")
