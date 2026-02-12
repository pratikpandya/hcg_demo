import boto3
import json

REGION = 'ap-southeast-1'

bedrock = boto3.client('bedrock', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

# List available embedding models
print("Available embedding models in ap-southeast-1:\n")
try:
    models = bedrock.list_foundation_models()
    embed_models = [m for m in models['modelSummaries'] if 'embed' in m['modelId'].lower()]
    for m in embed_models:
        print(f"  - {m['modelId']}")
    
    if embed_models:
        # Use the first available embedding model
        model_id = embed_models[0]['modelId']
        model_arn = f"arn:aws:bedrock:{REGION}::foundation-model/{model_id}"
        print(f"\n✅ Using: {model_id}")
        
        # Update all Knowledge Bases
        with open('hcg_demo_knowledge_bases.json', 'r') as f:
            kbs = json.load(f)
        
        print("\nUpdating Knowledge Bases with correct model...\n")
        for domain, kb_data in kbs.items():
            kb_id = kb_data['knowledge_base_id']
            print(f"{domain.upper()}: {kb_id}")
            try:
                # Get current KB config
                kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
                
                # Update with correct model
                bedrock_agent.update_knowledge_base(
                    knowledgeBaseId=kb_id,
                    name=kb['knowledgeBase']['name'],
                    roleArn=kb['knowledgeBase']['roleArn'],
                    knowledgeBaseConfiguration={
                        'type': 'VECTOR',
                        'vectorKnowledgeBaseConfiguration': {
                            'embeddingModelArn': model_arn
                        }
                    },
                    storageConfiguration=kb['knowledgeBase']['storageConfiguration']
                )
                print(f"  ✅ Updated\n")
            except Exception as e:
                print(f"  ❌ {str(e)[:150]}\n")
    
except Exception as e:
    print(f"Error: {e}")
