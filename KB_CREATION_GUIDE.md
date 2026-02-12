# Knowledge Base Creation Guide - AWS Console

## Quick Summary
Create 4 Knowledge Bases via AWS Bedrock Console. Each takes ~2 minutes.

## Prerequisites (Already Done ✅)
- ✅ S3 Bucket: hcg-demo-knowledge-026138522123
- ✅ Documents uploaded to S3:
  - hr-docs/ (2 files)
  - it-docs/ (3 files)
  - finance-docs/ (2 files)
  - general-docs/ (3 files)
- ✅ OpenSearch Collection: hcg-demo-knowledge (y3f4j35z37u9awc6sqkc)
- ✅ IAM Role: hcg-demo-bedrock-agent

## Steps for Each Knowledge Base

### 1. HR Knowledge Base

1. Go to: https://ap-southeast-1.console.aws.amazon.com/bedrock/home?region=ap-southeast-1#/knowledge-bases
2. Click **"Create knowledge base"**
3. **Knowledge base details:**
   - Name: `HCG-Demo-HR-KB`
   - Description: `HR policies, benefits, and leave information`
   - IAM Role: Select **"Use an existing service role"**
   - Role ARN: `arn:aws:iam::026138522123:role/hcg-demo-bedrock-agent`
   - Click **Next**

4. **Set up data source:**
   - Data source name: `HCG-Demo-HR-DS`
   - S3 URI: `s3://hcg-demo-knowledge-026138522123/hr-docs/`
   - Click **Next**

5. **Select embeddings model:**
   - Embeddings model: **Titan Embeddings G1 - Text**
   - Click **Next**

6. **Configure vector store:**
   - Vector database: **Amazon OpenSearch Serverless**
   - Select existing collection: **hcg-demo-knowledge**
   - Vector index name: `hcg-kb-hr` (or leave auto-generated)
   - Vector field: `vector`
   - Text field: `text`
   - Metadata field: `metadata`
   - Click **Next**

7. **Review and create:**
   - Review settings
   - Click **Create knowledge base**

8. **Sync data source:**
   - After creation, click **"Sync"** button
   - Wait 2-3 minutes for ingestion to complete

9. **Copy Knowledge Base ID** (format: XXXXXXXXXX)

### 2. IT Knowledge Base
Repeat steps 1-9 with:
- Name: `HCG-Demo-IT-KB`
- Description: `IT support guides and troubleshooting`
- Data source: `HCG-Demo-IT-DS`
- S3 URI: `s3://hcg-demo-knowledge-026138522123/it-docs/`
- Vector index: `hcg-kb-it`

### 3. Finance Knowledge Base
Repeat steps 1-9 with:
- Name: `HCG-Demo-Finance-KB`
- Description: `Finance policies and procedures`
- Data source: `HCG-Demo-Finance-DS`
- S3 URI: `s3://hcg-demo-knowledge-026138522123/finance-docs/`
- Vector index: `hcg-kb-finance`

### 4. General Knowledge Base
Repeat steps 1-9 with:
- Name: `HCG-Demo-General-KB`
- Description: `General company information and FAQs`
- Data source: `HCG-Demo-General-DS`
- S3 URI: `s3://hcg-demo-knowledge-026138522123/general-docs/`
- Vector index: `hcg-kb-general`

## After Creation

Once all 4 Knowledge Bases are created, run this command to save the IDs:

```bash
python check_kb_status.py
```

This will verify all 4 KBs are created and save their IDs to `hcg_demo_knowledge_bases.json`.

## Estimated Time
- Total: ~10-15 minutes (2-3 minutes per KB)
- Can be done in parallel if you open multiple browser tabs

## Troubleshooting

**If "Sync" fails:**
- Check IAM role has S3 read permissions
- Verify S3 bucket path is correct
- Check OpenSearch data access policy includes the Bedrock role

**If OpenSearch collection not found:**
- Verify collection name: hcg-demo-knowledge
- Check region: ap-southeast-1

**If IAM role not found:**
- Verify role exists: hcg-demo-bedrock-agent
- Check role has Bedrock and OpenSearch permissions
