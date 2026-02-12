import boto3
import json

events = boto3.client('events', region_name='ap-southeast-1')
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
iam = boto3.client('iam', region_name='ap-southeast-1')

def create_daily_sync_rule():
    # Create EventBridge rule for daily sync at 2 AM SGT
    rule_name = 'hcg-demo-daily-content-sync'
    
    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression='cron(0 18 * * ? *)',  # 2 AM SGT = 6 PM UTC
        State='ENABLED',
        Description='Daily sync from SharePoint/Confluence to Knowledge Bases'
    )
    
    print(f"✅ Created EventBridge rule: {rule_name}")
    return response['RuleArn']

def create_quarterly_review_rule():
    # Create EventBridge rule for quarterly review on 1st of every quarter
    rule_name = 'hcg-demo-quarterly-review'
    
    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression='cron(0 2 1 1,4,7,10 ? *)',  # 1st Jan, Apr, Jul, Oct at 10 AM SGT
        State='ENABLED',
        Description='Quarterly content review notification'
    )
    
    print(f"✅ Created EventBridge rule: {rule_name}")
    return response['RuleArn']

def create_weekly_pending_review_rule():
    # Create EventBridge rule for weekly pending review check
    rule_name = 'hcg-demo-weekly-review-check'
    
    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression='cron(0 1 ? * MON *)',  # Every Monday at 9 AM SGT
        State='ENABLED',
        Description='Weekly check for pending document reviews'
    )
    
    print(f"✅ Created EventBridge rule: {rule_name}")
    return response['RuleArn']

def add_lambda_targets():
    # Add Lambda targets to rules
    events.put_targets(
        Rule='hcg-demo-daily-content-sync',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:ap-southeast-1:026138522123:function:hcg-demo-content-sync',
            'Input': json.dumps({'source': 'sharepoint', 'domain': 'all'})
        }]
    )
    
    events.put_targets(
        Rule='hcg-demo-quarterly-review',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:ap-southeast-1:026138522123:function:hcg-demo-content-governance',
            'Input': json.dumps({'action': 'get_pending_reviews'})
        }]
    )
    
    events.put_targets(
        Rule='hcg-demo-weekly-review-check',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:ap-southeast-1:026138522123:function:hcg-demo-content-governance',
            'Input': json.dumps({'action': 'get_pending_reviews'})
        }]
    )
    
    print("✅ Added Lambda targets to EventBridge rules")

def add_lambda_permissions():
    # Add permissions for EventBridge to invoke Lambda
    functions = [
        'hcg-demo-content-sync',
        'hcg-demo-content-governance'
    ]
    
    for func in functions:
        try:
            lambda_client.add_permission(
                FunctionName=func,
                StatementId=f'EventBridge-{func}',
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com'
            )
            print(f"✅ Added EventBridge permission to {func}")
        except lambda_client.exceptions.ResourceConflictException:
            print(f"✅ Permission already exists for {func}")

if __name__ == '__main__':
    print("Creating EventBridge schedules for content governance...")
    
    daily_arn = create_daily_sync_rule()
    quarterly_arn = create_quarterly_review_rule()
    weekly_arn = create_weekly_pending_review_rule()
    
    print("\n✅ All EventBridge rules created successfully")
    print(f"\nSchedules:")
    print(f"  - Daily sync: 2 AM SGT (6 PM UTC)")
    print(f"  - Quarterly review: 1st of Jan/Apr/Jul/Oct at 10 AM SGT")
    print(f"  - Weekly review check: Every Monday at 9 AM SGT")
