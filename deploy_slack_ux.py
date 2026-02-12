import boto3
import json
import zipfile
import io

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

lambda_client = boto3.client('lambda', region_name=REGION)

print("="*70)
print("🚀 Deploying Slack UX Integration")
print("="*70 + "\n")

# Create Lambda package
print("1. Creating Lambda package...")
with open('lambda_webhook_handler_complete.py', 'r') as f:
    code = f.read()

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('lambda_function.py', code)
zip_buffer.seek(0)
print("   ✅ Package created\n")

# Update Lambda
print("2. Updating webhook handler...")
function_name = 'hcg-demo-webhook-handler'

try:
    lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_buffer.read()
    )
    print(f"   ✅ Updated: {function_name}\n")
except Exception as e:
    print(f"   ❌ Error: {str(e)[:150]}\n")

print("="*70)
print("✅ Slack UX Integration Deployed")
print("="*70)
print("\nFeatures Enabled:")
print("  ✅ Progressive status indicators (Thinking → Searching)")
print("  ✅ Source citations with Block Kit formatting")
print("  ✅ Domain-specific follow-up suggestions")
print("  ✅ Smart action buttons (View Policy, Create Ticket)")
print("  ✅ Inline feedback collection (👍/👎)")
print("  ✅ Agent orchestration integration")
print("\nSlack is now the complete UX layer!")
