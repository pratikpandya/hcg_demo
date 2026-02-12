import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')

# Test queries covering redirectional patterns (65% of volume)
TEST_QUERIES = [
    {'query': 'how do i submit an expense report', 'domain': 'finance', 'expected': 'concur'},
    {'query': 'where can i request leave', 'domain': 'hr', 'expected': 'workday'},
    {'query': 'create an it ticket', 'domain': 'it', 'expected': 'servicenow'},
    {'query': 'access vpn portal', 'domain': 'it', 'expected': 'vpn'},
    {'query': 'view company policies', 'domain': 'general', 'expected': 'hubbahub'},
    {'query': 'submit travel request', 'domain': 'finance', 'expected': 'concur'},
    {'query': 'check my payslip', 'domain': 'hr', 'expected': 'workday'},
    {'query': 'search confluence wiki', 'domain': 'general', 'expected': 'confluence'}
]

def test_deep_linking():
    print("Testing Deep Linking Infrastructure...\n")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\nTest {i}: {test['query']}")
        print(f"Domain: {test['domain']}")
        
        response = lambda_client.invoke(
            FunctionName='hcg-demo-deep-linking',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'generate_link',
                'query': test['query'],
                'domain': test['domain'],
                'user_email': 'test@company.com'
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        # Handle Lambda error response
        if 'errorMessage' in result:
            print(f"❌ FAIL - Lambda error: {result.get('errorMessage')}")
            failed += 1
            continue
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            resource_id = body['resource_id']
            
            if test['expected'] in resource_id:
                print(f"✅ PASS - Matched: {body['resource_name']}")
                print(f"   Link: {body['link']}")
                print(f"   SSO: {'Enabled' if body['sso_enabled'] else 'Disabled'}")
                passed += 1
            else:
                print(f"❌ FAIL - Expected {test['expected']}, got {resource_id}")
                failed += 1
        else:
            print(f"❌ FAIL - No resource found")
            failed += 1
    
    print("\n" + "="*60)
    print(f"\nTest Results: {passed}/{len(TEST_QUERIES)} passed")
    print(f"Success Rate: {(passed/len(TEST_QUERIES)*100):.1f}%")
    
    return passed == len(TEST_QUERIES)

def test_health_check():
    print("\n\nTesting Link Health Check...\n")
    print("="*60)
    
    response = lambda_client.invoke(
        FunctionName='hcg-demo-link-health-check',
        InvocationType='RequestResponse',
        Payload=json.dumps({})
    )
    
    result = json.loads(response['Payload'].read())
    body = json.loads(result['body'])
    
    print(f"Total resources: {body['total']}")
    print(f"Healthy: {body['healthy']}")
    print(f"Unhealthy: {body['unhealthy']}")
    
    print("\nHealth check details:")
    for check in body['checks'][:5]:  # Show first 5
        status_icon = "✅" if check['status'] == 'healthy' else "❌"
        print(f"  {status_icon} {check['resource_name']}: {check['status']} ({check['response_time_ms']}ms)")
    
    return True

if __name__ == '__main__':
    deep_linking_ok = test_deep_linking()
    health_check_ok = test_health_check()
    
    print("\n" + "="*60)
    if deep_linking_ok and health_check_ok:
        print("✅ All tests passed!")
    else:
        print("⚠️ Some tests failed")
    print("="*60)
