import boto3
import zipfile
import io
import json

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
iam = boto3.client('iam', region_name='ap-southeast-1')

print("="*70)
print("UPDATING SERVICENOW LAMBDA FUNCTION")
print("="*70)

# Step 1: Update IAM role to allow SSM access
print("\nStep 1: Updating IAM role permissions...")
role_name = 'hcg-demo-lambda-role'

try:
    # Attach SSM policy
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess'
    )
    print(f"✅ Attached SSM read policy to {role_name}")
except iam.exceptions.NoSuchEntityException:
    print(f"⚠️ Role {role_name} not found, using default Lambda role")
except Exception as e:
    if 'already attached' in str(e).lower():
        print(f"✅ SSM policy already attached to {role_name}")
    else:
        print(f"⚠️ Warning: {str(e)}")

# Step 2: Create deployment package
print("\nStep 2: Creating deployment package...")
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    with open('lambda_servicenow_action_updated.py', 'r') as f:
        zip_file.writestr('lambda_function.py', f.read())

zip_buffer.seek(0)
print("✅ Deployment package created")

# Step 3: Update Lambda function
print("\nStep 3: Updating Lambda function code...")
function_name = 'hcg-demo-servicenow-action'

try:
    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_buffer.read()
    )
    print(f"✅ Updated Lambda function: {function_name}")
    print(f"   Version: {response['Version']}")
    print(f"   Last Modified: {response['LastModified']}")
    
    # Update timeout to 30 seconds
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        Timeout=30,
        Description='ServiceNow integration with Parameter Store credentials'
    )
    print(f"✅ Updated function configuration (timeout: 30s)")
    
except lambda_client.exceptions.ResourceNotFoundException:
    print(f"❌ Lambda function {function_name} not found")
    print("   Creating new function...")
    
    # Get IAM role ARN
    try:
        role_response = iam.get_role(RoleName=role_name)
        role_arn = role_response['Role']['Arn']
    except:
        print("❌ Could not find IAM role. Please create Lambda function manually.")
        exit(1)
    
    zip_buffer.seek(0)
    response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=30,
        MemorySize=256,
        Description='ServiceNow integration with Parameter Store credentials'
    )
    print(f"✅ Created Lambda function: {function_name}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    exit(1)

print("\n" + "="*70)
print("✅ ServiceNow Lambda function updated successfully!")
print("="*70)
print("\nNext steps:")
print("1. Test ServiceNow integration")
print("\nRun: python test_servicenow_integration.py")
