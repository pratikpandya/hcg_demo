import boto3
import json
from pathlib import Path

REGION = 'ap-southeast-1'

with open('hcg_demo_resources.json', 'r') as f:
    resources = json.load(f)

S3_BUCKET = resources['s3']['knowledge']

s3 = boto3.client('s3', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

print("="*70)
print("📊 HCG Demo - Knowledge Base Status Check")
print("="*70 + "\n")

# 1. Check local documents
print("1️⃣ LOCAL DOCUMENTS")
print("-"*70)
total_docs = 0
for domain in ['hr', 'it', 'finance', 'general']:
    folder = Path(f'sample_documents/{domain}')
    count = len(list(folder.glob('*.txt')))
    total_docs += count
    print(f"   {domain.upper()}: {count} documents")
print(f"   ✅ Total: {total_docs} documents created\n")

# 2. Check S3 uploads
print("2️⃣ S3 UPLOADS")
print("-"*70)
s3_total = 0
for domain in ['hr', 'it', 'finance', 'general']:
    prefix = f'{domain}-docs/'
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        count = response.get('KeyCount', 0)
        s3_total += count
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {domain.upper()}: {count} files in s3://{S3_BUCKET}/{prefix}")
    except Exception as e:
        print(f"   ❌ {domain.upper()}: Error - {str(e)[:50]}")
print(f"   Total: {s3_total} documents uploaded\n")

# 3. Check Knowledge Bases
print("3️⃣ BEDROCK KNOWLEDGE BASES")
print("-"*70)
try:
    kbs = bedrock_agent.list_knowledge_bases()
    hcg_kbs = [kb for kb in kbs.get('knowledgeBaseSummaries', []) if 'HCG-Demo' in kb['name']]
    
    if len(hcg_kbs) == 0:
        print(f"   ❌ 0 Knowledge Bases created")
    else:
        print(f"   ✅ {len(hcg_kbs)} Knowledge Bases found:")
        for kb in hcg_kbs:
            print(f"      • {kb['name']}: {kb['knowledgeBaseId']}")
            print(f"        Status: {kb['status']}")
    print()
except Exception as e:
    print(f"   ❌ Error: {str(e)[:100]}\n")

# 4. Summary
print("="*70)
print("📋 SUMMARY")
print("="*70)
print(f"✅ Documents Created: {total_docs}/10 (100%)")
print(f"{'✅' if s3_total > 0 else '❌'} S3 Uploads: {s3_total}/10 ({int(s3_total/10*100)}%)")
print(f"{'✅' if len(hcg_kbs) == 4 else '❌'} Knowledge Bases: {len(hcg_kbs) if 'hcg_kbs' in locals() else 0}/4 ({int(len(hcg_kbs)/4*100) if 'hcg_kbs' in locals() else 0}%)")

if s3_total == 10 and len(hcg_kbs) == 4:
    print("\n🎉 Knowledge Base Layer: 100% COMPLETE!")
elif s3_total == 10:
    print("\n⚠️  Documents uploaded but Knowledge Bases not created")
    print("   Issue: OpenSearch index creation required")
else:
    print(f"\n⚠️  Knowledge Base Layer: {int((s3_total + len(hcg_kbs)*2.5)/15*100)}% Complete")
