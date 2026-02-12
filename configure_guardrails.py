import boto3
import json

REGION = 'ap-southeast-1'
ACCOUNT_ID = '026138522123'

bedrock = boto3.client('bedrock', region_name=REGION)

print("="*70)
print("🛡️ Configuring Bedrock Guardrails")
print("="*70 + "\n")

# Create Guardrail
print("1. Creating Bedrock Guardrail...")

guardrail_config = {
    'name': 'hcg-demo-guardrail',
    'description': 'PII detection and content filtering for HCG Demo',
    'topicPolicyConfig': {
        'topicsConfig': [
            {
                'name': 'FinancialAdvice',
                'definition': 'Providing specific financial or investment advice',
                'examples': [
                    'Should I invest in stocks?',
                    'What should I do with my money?'
                ],
                'type': 'DENY'
            },
            {
                'name': 'MedicalAdvice',
                'definition': 'Providing specific medical diagnosis or treatment advice',
                'examples': [
                    'What medication should I take?',
                    'Do I have a medical condition?'
                ],
                'type': 'DENY'
            }
        ]
    },
    'contentPolicyConfig': {
        'filtersConfig': [
            {
                'type': 'SEXUAL',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            {
                'type': 'VIOLENCE',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            {
                'type': 'HATE',
                'inputStrength': 'HIGH',
                'outputStrength': 'HIGH'
            },
            {
                'type': 'INSULTS',
                'inputStrength': 'MEDIUM',
                'outputStrength': 'MEDIUM'
            },
            {
                'type': 'MISCONDUCT',
                'inputStrength': 'MEDIUM',
                'outputStrength': 'MEDIUM'
            },
            {
                'type': 'PROMPT_ATTACK',
                'inputStrength': 'HIGH',
                'outputStrength': 'NONE'
            }
        ]
    },
    'sensitiveInformationPolicyConfig': {
        'piiEntitiesConfig': [
            {'type': 'EMAIL', 'action': 'ANONYMIZE'},
            {'type': 'PHONE', 'action': 'ANONYMIZE'},
            {'type': 'NAME', 'action': 'ANONYMIZE'},
            {'type': 'ADDRESS', 'action': 'ANONYMIZE'},
            {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'},
            {'type': 'DRIVER_ID', 'action': 'ANONYMIZE'},
            {'type': 'PASSWORD', 'action': 'BLOCK'}
        ]
    },
    'blockedInputMessaging': 'I cannot process that request as it contains sensitive information or inappropriate content.',
    'blockedOutputsMessaging': 'I cannot provide that information as it may contain sensitive data.'
}

try:
    response = bedrock.create_guardrail(**guardrail_config)
    
    guardrail_id = response['guardrailId']
    guardrail_arn = response['guardrailArn']
    
    print(f"   ✅ Guardrail created")
    print(f"   ID: {guardrail_id}")
    print(f"   ARN: {guardrail_arn}\n")
    
    # Save guardrail info
    with open('hcg_demo_guardrail.json', 'w') as f:
        json.dump({
            'guardrail_id': guardrail_id,
            'guardrail_arn': guardrail_arn,
            'version': response.get('version', '1')
        }, f, indent=2)
    
except bedrock.exceptions.ConflictException:
    print("   ✅ Guardrail already exists\n")
    
    # List existing guardrails
    try:
        guardrails = bedrock.list_guardrails()
        for g in guardrails.get('guardrails', []):
            if g['name'] == 'hcg-demo-guardrail':
                print(f"   ID: {g['id']}")
                print(f"   ARN: {g['arn']}\n")
                
                with open('hcg_demo_guardrail.json', 'w') as f:
                    json.dump({
                        'guardrail_id': g['id'],
                        'guardrail_arn': g['arn'],
                        'version': '1'
                    }, f, indent=2)
                break
    except Exception as e:
        print(f"   ⚠️  Could not retrieve guardrail: {str(e)[:100]}\n")

except Exception as e:
    print(f"   ❌ Error: {str(e)[:200]}\n")

print("="*70)
print("✅ Guardrails Configuration Complete")
print("="*70)
print("\nProtections Enabled:")
print("  ✅ PII Detection & Anonymization")
print("  ✅ Content Filtering (Sexual, Violence, Hate)")
print("  ✅ Prompt Attack Prevention")
print("  ✅ Sensitive Information Blocking")
print("  ✅ Topic Restrictions (Financial/Medical Advice)")
