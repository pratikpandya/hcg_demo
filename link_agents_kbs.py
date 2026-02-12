import boto3
import json

REGION = 'ap-southeast-1'

bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

# Load resources
with open('hcg_demo_agents.json', 'r') as f:
    agents = json.load(f)

with open('hcg_demo_knowledge_bases.json', 'r') as f:
    kbs = json.load(f)

print("="*70)
print("🔗 Linking Knowledge Bases to Agents")
print("="*70 + "\n")

# Map agents to KBs
agent_kb_mapping = {
    'hcg-demo-hr-agent': 'hr',
    'hcg-demo-it-agent': 'it',
    'hcg-demo-finance-agent': 'finance',
    'hcg-demo-general-agent': 'general'
}

results = {}

for agent_name, kb_domain in agent_kb_mapping.items():
    agent_id = agents[agent_name]
    kb_id = kbs[kb_domain]['knowledge_base_id']
    
    print(f"{agent_name}")
    print(f"  Agent: {agent_id}")
    print(f"  KB: {kb_id}")
    
    try:
        # Associate KB with agent
        response = bedrock_agent.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion='DRAFT',
            knowledgeBaseId=kb_id,
            description=f'{kb_domain.upper()} knowledge base',
            knowledgeBaseState='ENABLED'
        )
        
        kb_association_id = response['agentKnowledgeBase']['knowledgeBaseId']
        print(f"  ✅ Linked\n")
        
        results[agent_name] = {
            'agent_id': agent_id,
            'kb_id': kb_id,
            'kb_association_id': kb_association_id,
            'status': 'linked'
        }
        
    except Exception as e:
        error = str(e)
        if 'already associated' in error.lower():
            print(f"  ✅ Already linked\n")
            results[agent_name] = {'agent_id': agent_id, 'kb_id': kb_id, 'status': 'already_linked'}
        else:
            print(f"  ❌ {error[:150]}\n")
            results[agent_name] = {'agent_id': agent_id, 'kb_id': kb_id, 'status': 'failed', 'error': error[:150]}

# Save results
with open('agent_kb_links.json', 'w') as f:
    json.dump(results, f, indent=2)

print("="*70)
print(f"✅ Linked {len([r for r in results.values() if r['status'] in ['linked', 'already_linked']])}/4 agents to KBs")
print("="*70)
