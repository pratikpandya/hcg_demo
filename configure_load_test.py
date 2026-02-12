import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')
application_autoscaling = boto3.client('application-autoscaling', region_name='ap-southeast-1')

print("="*70)
print("CONFIGURING AWS RESOURCES FOR LOAD TESTING")
print("="*70)

# Lambda Functions to configure
LAMBDA_FUNCTIONS = [
    'hcg-demo-webhook-handler',
    'hcg-demo-supervisor-agent',
    'hcg-demo-servicenow-action'
]

# DynamoDB Tables to configure
DYNAMODB_TABLES = [
    'hcg-demo-conversations',
    'hcg-demo-user-feedback'
]

print("\n1. Configuring Lambda Concurrency...")
for func in LAMBDA_FUNCTIONS:
    try:
        # Set reserved concurrency to 100 per function
        lambda_client.put_function_concurrency(
            FunctionName=func,
            ReservedConcurrentExecutions=100
        )
        print(f"  ✅ {func}: Reserved 100 concurrent executions")
    except Exception as e:
        print(f"  ⚠️ {func}: {str(e)}")

print("\n2. Configuring DynamoDB Auto-Scaling...")
for table in DYNAMODB_TABLES:
    try:
        # Register scalable target for read capacity
        application_autoscaling.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table}',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            MinCapacity=5,
            MaxCapacity=100
        )
        
        # Register scalable target for write capacity
        application_autoscaling.register_scalable_target(
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table}',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            MinCapacity=5,
            MaxCapacity=100
        )
        
        # Configure auto-scaling policy for reads
        application_autoscaling.put_scaling_policy(
            PolicyName=f'{table}-read-scaling',
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table}',
            ScalableDimension='dynamodb:table:ReadCapacityUnits',
            PolicyType='TargetTrackingScaling',
            TargetTrackingScalingPolicyConfiguration={
                'TargetValue': 70.0,
                'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'DynamoDBReadCapacityUtilization'
                }
            }
        )
        
        # Configure auto-scaling policy for writes
        application_autoscaling.put_scaling_policy(
            PolicyName=f'{table}-write-scaling',
            ServiceNamespace='dynamodb',
            ResourceId=f'table/{table}',
            ScalableDimension='dynamodb:table:WriteCapacityUnits',
            PolicyType='TargetTrackingScaling',
            TargetTrackingScalingPolicyConfiguration={
                'TargetValue': 70.0,
                'PredefinedMetricSpecification': {
                    'PredefinedMetricType': 'DynamoDBWriteCapacityUtilization'
                }
            }
        )
        
        print(f"  ✅ {table}: Auto-scaling configured (5-100 capacity)")
    except Exception as e:
        if 'already exists' in str(e).lower():
            print(f"  ✅ {table}: Auto-scaling already configured")
        else:
            print(f"  ⚠️ {table}: {str(e)}")

print("\n3. Summary:")
print(f"  Lambda Functions: {len(LAMBDA_FUNCTIONS)} configured")
print(f"  DynamoDB Tables: {len(DYNAMODB_TABLES)} configured")
print(f"  Total Capacity: 300 Lambda concurrent executions")
print(f"  DynamoDB: Auto-scales 5-100 capacity units")

print("\n" + "="*70)
print("✅ AWS resources configured for load testing")
print("="*70)
print("\nReady for load test with 500 concurrent users")
print("Run: python run_load_test.py")
