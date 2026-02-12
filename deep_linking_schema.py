import boto3
import json

dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')

def create_resource_catalog_table():
    try:
        response = dynamodb.create_table(
            TableName='hcg-demo-resource-catalog',
            KeySchema=[
                {'AttributeName': 'resource_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'resource_id', 'AttributeType': 'S'},
                {'AttributeName': 'category', 'AttributeType': 'S'},
                {'AttributeName': 'domain', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'category-index',
                    'KeySchema': [{'AttributeName': 'category', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'domain-index',
                    'KeySchema': [{'AttributeName': 'domain', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✅ Created table: hcg-demo-resource-catalog")
        return response['TableDescription']['TableArn']
    except dynamodb.exceptions.ResourceInUseException:
        print("✅ Table already exists: hcg-demo-resource-catalog")
        return None

def create_link_health_table():
    try:
        response = dynamodb.create_table(
            TableName='hcg-demo-link-health',
            KeySchema=[
                {'AttributeName': 'resource_id', 'KeyType': 'HASH'},
                {'AttributeName': 'check_timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'resource_id', 'AttributeType': 'S'},
                {'AttributeName': 'check_timestamp', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✅ Created table: hcg-demo-link-health")
        return response['TableDescription']['TableArn']
    except dynamodb.exceptions.ResourceInUseException:
        print("✅ Table already exists: hcg-demo-link-health")
        return None

if __name__ == '__main__':
    print("Creating Deep Linking tables...")
    catalog_arn = create_resource_catalog_table()
    health_arn = create_link_health_table()
    print("\n✅ Deep Linking schema created successfully")
