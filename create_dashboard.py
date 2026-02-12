import boto3
import json

REGION = 'ap-southeast-1'

cloudwatch = boto3.client('cloudwatch', region_name=REGION)

print("="*70)
print("📊 Creating CloudWatch Dashboard")
print("="*70 + "\n")

dashboard_body = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Total Requests"}],
                    [".", "Errors", {"stat": "Sum", "label": "Errors"}],
                    [".", "Throttles", {"stat": "Sum", "label": "Throttles"}]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": REGION,
                "title": "Request Volume & Errors",
                "period": 300
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/Lambda", "Duration", {"stat": "Average", "label": "Avg Latency"}],
                    ["...", {"stat": "p99", "label": "P99 Latency"}]
                ],
                "view": "timeSeries",
                "region": REGION,
                "title": "Response Latency",
                "period": 300,
                "yAxis": {"left": {"label": "ms"}}
            }
        },
        {
            "type": "log",
            "properties": {
                "query": f"SOURCE '/aws/lambda/hcg-demo-supervisor-orchestrator'\n| fields @timestamp, domain, confidence\n| stats count() by domain",
                "region": REGION,
                "title": "Queries by Domain",
                "stacked": False
            }
        },
        {
            "type": "log",
            "properties": {
                "query": f"SOURCE '/aws/lambda/hcg-demo-supervisor-orchestrator'\n| fields @timestamp, confidence_level\n| stats count() by confidence_level",
                "region": REGION,
                "title": "Confidence Distribution",
                "stacked": False
            }
        },
        {
            "type": "log",
            "properties": {
                "query": f"SOURCE '/aws/lambda/hcg-demo-webhook-handler'\n| filter feedback = 'helpful' or feedback = 'not_helpful'\n| stats count() by feedback",
                "region": REGION,
                "title": "User Feedback",
                "stacked": False
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["HCG-Demo", "RoutingAccuracy", {"stat": "Average"}],
                    [".", "ResponseQuality", {"stat": "Average"}],
                    [".", "UserSatisfaction", {"stat": "Average"}]
                ],
                "view": "singleValue",
                "region": REGION,
                "title": "Quality Metrics",
                "period": 86400
            }
        }
    ]
}

try:
    cloudwatch.put_dashboard(
        DashboardName='HCG-Demo-Metrics',
        DashboardBody=json.dumps(dashboard_body)
    )
    print("✅ Dashboard created: HCG-Demo-Metrics")
    print(f"   URL: https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=HCG-Demo-Metrics\n")
except Exception as e:
    print(f"❌ Error: {str(e)[:200]}\n")

# Create metric filters
print("Creating metric filters...")

logs = boto3.client('logs', region_name=REGION)

filters = [
    {
        'name': 'RoutingAccuracy',
        'pattern': '[timestamp, request_id, level, msg, domain, expected, actual, match]',
        'metric_name': 'RoutingAccuracy',
        'metric_value': '$match'
    },
    {
        'name': 'LowConfidenceResponses',
        'pattern': '[timestamp, request_id, level, msg, confidence_level = "low"]',
        'metric_name': 'LowConfidenceCount',
        'metric_value': '1'
    },
    {
        'name': 'FallbackResponses',
        'pattern': '[timestamp, request_id, level, msg, safe_to_respond = "False"]',
        'metric_name': 'FallbackCount',
        'metric_value': '1'
    }
]

for f in filters:
    try:
        logs.put_metric_filter(
            logGroupName='/aws/lambda/hcg-demo-supervisor-orchestrator',
            filterName=f['name'],
            filterPattern=f['pattern'],
            metricTransformations=[{
                'metricName': f['metric_name'],
                'metricNamespace': 'HCG-Demo',
                'metricValue': f['metric_value']
            }]
        )
        print(f"  ✅ {f['name']}")
    except logs.exceptions.ResourceAlreadyExistsException:
        print(f"  ✅ {f['name']} (already exists)")
    except Exception as e:
        print(f"  ❌ {f['name']}: {str(e)[:100]}")

print("\n" + "="*70)
print("✅ Dashboard & Metrics Complete")
print("="*70)
