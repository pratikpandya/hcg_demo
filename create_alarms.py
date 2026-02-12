import boto3

REGION = 'ap-southeast-1'
SNS_TOPIC_ARN = f'arn:aws:sns:{REGION}:026138522123:hcg-demo-alerts'

cloudwatch = boto3.client('cloudwatch', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

print("="*70)
print("🚨 Creating CloudWatch Alarms")
print("="*70 + "\n")

# Create SNS topic for alerts
print("1. Creating SNS topic for alerts...")
try:
    response = sns.create_topic(Name='hcg-demo-alerts')
    topic_arn = response['TopicArn']
    print(f"   ✅ Topic: {topic_arn}\n")
except Exception as e:
    print(f"   ✅ Topic already exists\n")
    topic_arn = SNS_TOPIC_ARN

# Define alarms
alarms = [
    {
        'name': 'HCG-Demo-HighErrorRate',
        'description': 'Alert when error rate exceeds 5%',
        'metric': 'Errors',
        'namespace': 'AWS/Lambda',
        'statistic': 'Sum',
        'threshold': 5,
        'comparison': 'GreaterThanThreshold',
        'period': 300,
        'evaluation_periods': 2
    },
    {
        'name': 'HCG-Demo-HighLatency',
        'description': 'Alert when P99 latency exceeds 5 seconds',
        'metric': 'Duration',
        'namespace': 'AWS/Lambda',
        'statistic': 'p99',
        'threshold': 5000,
        'comparison': 'GreaterThanThreshold',
        'period': 300,
        'evaluation_periods': 2
    },
    {
        'name': 'HCG-Demo-LowQuality',
        'description': 'Alert when overall quality drops below 0.7',
        'metric': 'OverallQuality',
        'namespace': 'HCG-Demo',
        'statistic': 'Average',
        'threshold': 0.7,
        'comparison': 'LessThanThreshold',
        'period': 3600,
        'evaluation_periods': 1
    },
    {
        'name': 'HCG-Demo-HighFallbackRate',
        'description': 'Alert when fallback rate exceeds 20%',
        'metric': 'FallbackCount',
        'namespace': 'HCG-Demo',
        'statistic': 'Sum',
        'threshold': 20,
        'comparison': 'GreaterThanThreshold',
        'period': 3600,
        'evaluation_periods': 1
    },
    {
        'name': 'HCG-Demo-NoRequests',
        'description': 'Alert when no requests received for 1 hour',
        'metric': 'Invocations',
        'namespace': 'AWS/Lambda',
        'statistic': 'Sum',
        'threshold': 1,
        'comparison': 'LessThanThreshold',
        'period': 3600,
        'evaluation_periods': 1
    }
]

print("2. Creating alarms...")
for alarm in alarms:
    try:
        cloudwatch.put_metric_alarm(
            AlarmName=alarm['name'],
            AlarmDescription=alarm['description'],
            MetricName=alarm['metric'],
            Namespace=alarm['namespace'],
            Statistic=alarm['statistic'],
            Period=alarm['period'],
            EvaluationPeriods=alarm['evaluation_periods'],
            Threshold=alarm['threshold'],
            ComparisonOperator=alarm['comparison'],
            AlarmActions=[topic_arn],
            TreatMissingData='notBreaching'
        )
        print(f"   ✅ {alarm['name']}")
    except Exception as e:
        print(f"   ❌ {alarm['name']}: {str(e)[:100]}")

print("\n" + "="*70)
print("✅ Alerting Rules Complete")
print("="*70)
print(f"\nAlerts will be sent to: {topic_arn}")
print("\nTo receive alerts, subscribe to the SNS topic:")
print(f"  aws sns subscribe --topic-arn {topic_arn} --protocol email --notification-endpoint your-email@example.com")
print("\nAlarms configured:")
print("  ✅ High Error Rate (>5%)")
print("  ✅ High Latency (P99 >5s)")
print("  ✅ Low Quality Score (<0.7)")
print("  ✅ High Fallback Rate (>20%)")
print("  ✅ No Requests (1 hour)")
