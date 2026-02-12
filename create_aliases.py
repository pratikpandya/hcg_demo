import boto3
import json
import time

REGION = 'ap-southeast-1'

bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)

with open('hcg_demo_agents.json', 'r') as f:
    agents = json.load(f)

print("Creating agent aliases...\n")

results = {}

for agent_name, agent_id in agents.items():
    if 'supervisor' in agent_name:
        continue
    
    print(f"{agent_name}: {agent_id}")
    
    try:
        # Create alias
        response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName='prod',
            description='Production alias'
        )
        
        alias_id = response['agentAlias']['agentAliasId']
        print(f"  ✅ Alias: {alias_id}\n")
        
        results[agent_name] = {
            'agent_id': agent_id,
            'alias_id': alias_id
        }
        
        time.sleep(2)
        
    except Exception as e:
        error = str(e)
        if 'already exists' in error.lower() or 'ResourceConflict' in error:
            # Get existing alias
            try:
                aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
                for alias in aliases['agentAliasSummaries']:
                    if alias['agentAliasName'] == 'prod':
                        alias_id = alias['agentAliasId']
                        print(f"  ✅ Existing alias: {alias_id}\n")
                        results[agent_name] = {'agent_id': agent_id, 'alias_id': alias_id}
                        break
            except:
                print(f"  ⚠️  {error[:100]}\n")
        else:
            print(f"  ❌ {error[:150]}\n")

with open('agent_aliases.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"✅ Created {len(results)} aliases")
