import boto3
import json
import time

REGION = 'ap-southeast-1'

lambda_client = boto3.client('lambda', region_name=REGION)

test_queries = [
    {"query": "How many days of annual leave do I get?", "expected_domain": "hr"},
    {"query": "How do I reset my password?", "expected_domain": "it"},
    {"query": "What is the expense reimbursement policy?", "expected_domain": "finance"},
    {"query": "Where is the office located?", "expected_domain": "general"}
]

print("="*70)
print("🧪 Testing Agent Orchestration & Routing")
print("="*70 + "\n")

results = []

for i, test in enumerate(test_queries, 1):
    print(f"Test {i}: {test['query']}")
    print(f"Expected: {test['expected_domain']}")
    
    try:
        response = lambda_client.invoke(
            FunctionName='hcg-demo-supervisor-orchestrator',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({
                    'query': test['query'],
                    'session_id': f'test-session-{i}'
                })
            })
        )
        
        payload = json.loads(response['Payload'].read())
        
        if payload['statusCode'] == 200:
            body = json.loads(payload['body'])
            domain = body.get('domain', 'unknown')
            confidence = body.get('confidence', 0)
            agent_response = body.get('response', '')
            citations = body.get('citations', [])
            
            match = "✅" if domain == test['expected_domain'] else "❌"
            print(f"Routed to: {domain} (confidence: {confidence}) {match}")
            print(f"Response: {agent_response[:150]}...")
            print(f"Citations: {len(citations)}")
            
            results.append({
                'query': test['query'],
                'expected': test['expected_domain'],
                'actual': domain,
                'match': domain == test['expected_domain'],
                'confidence': confidence,
                'citations': len(citations)
            })
        else:
            print(f"❌ Error: {payload}")
            results.append({'query': test['query'], 'match': False, 'error': payload})
    
    except Exception as e:
        print(f"❌ Exception: {str(e)[:150]}")
        results.append({'query': test['query'], 'match': False, 'error': str(e)[:150]})
    
    print()
    time.sleep(2)

# Summary
print("="*70)
print("📊 Test Results")
print("="*70)

matches = sum(1 for r in results if r.get('match', False))
total = len(results)

print(f"\nRouting Accuracy: {matches}/{total} ({int(matches/total*100)}%)")
print(f"\nDetails:")
for r in results:
    status = "✅" if r.get('match') else "❌"
    print(f"  {status} {r['query'][:50]}...")
    if 'actual' in r:
        print(f"     Expected: {r.get('expected')} | Actual: {r.get('actual')} | Confidence: {r.get('confidence')}")

with open('orchestration_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Results saved to orchestration_test_results.json")
