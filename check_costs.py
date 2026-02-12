import boto3
from datetime import datetime, timedelta

REGION = 'ap-southeast-1'

ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer only in us-east-1

# Get costs for last 30 days
end = datetime.now().date()
start = end - timedelta(days=30)

print("="*70)
print("💰 HCG Demo - AWS Cost Analysis")
print("="*70)
print(f"Period: {start} to {end}\n")

try:
    # Total cost
    response = ce.get_cost_and_usage(
        TimePeriod={'Start': str(start), 'End': str(end)},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        Filter={
            'Dimensions': {
                'Key': 'REGION',
                'Values': [REGION]
            }
        }
    )
    
    total = 0
    for result in response['ResultsByTime']:
        amount = float(result['Total']['UnblendedCost']['Amount'])
        total += amount
    
    print(f"Total Cost (Last 30 days): ${total:.2f}\n")
    
    # Cost by service
    response = ce.get_cost_and_usage(
        TimePeriod={'Start': str(start), 'End': str(end)},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
        Filter={
            'Dimensions': {
                'Key': 'REGION',
                'Values': [REGION]
            }
        }
    )
    
    print("Cost by Service:")
    print("-"*70)
    
    services = []
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            if amount > 0:
                services.append((service, amount))
    
    services.sort(key=lambda x: x[1], reverse=True)
    
    for service, amount in services:
        print(f"  {service:50s} ${amount:>8.2f}")
    
    print("-"*70)
    print(f"  {'TOTAL':50s} ${sum(s[1] for s in services):>8.2f}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nEstimated Monthly Costs (Based on Deployment):")
    print("-"*70)
    print(f"  {'OpenSearch Serverless (1 OCU)':50s} ${'175.00':>8s}")
    print(f"  {'DynamoDB (On-Demand, minimal)':50s} ${'1.00':>8s}")
    print(f"  {'S3 (10 docs, minimal)':50s} ${'0.10':>8s}")
    print(f"  {'Lambda (minimal invocations)':50s} ${'0.50':>8s}")
    print(f"  {'API Gateway (minimal)':50s} ${'0.50':>8s}")
    print(f"  {'CloudWatch Logs':50s} ${'2.00':>8s}")
    print(f"  {'Bedrock (4 KBs, no queries yet)':50s} ${'0.00':>8s}")
    print(f"  {'VPC (NAT Gateway)':50s} ${'45.00':>8s}")
    print(f"  {'Secrets Manager (2 secrets)':50s} ${'0.80':>8s}")
    print("-"*70)
    print(f"  {'ESTIMATED TOTAL':50s} ${'224.90':>8s}")
    print("\n⚠️  OpenSearch Serverless is the largest cost ($175/month)")
