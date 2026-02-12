import boto3
import zipfile
import io

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

# Update deep linking Lambda
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    with open('lambda_deep_linking.py', 'r') as f:
        zip_file.writestr('lambda_function.py', f.read())

zip_buffer.seek(0)

lambda_client.update_function_code(
    FunctionName='hcg-demo-deep-linking',
    ZipFile=zip_buffer.read()
)

print("✅ Updated hcg-demo-deep-linking Lambda function")
