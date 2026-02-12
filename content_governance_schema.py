import boto3
import json
from datetime import datetime

dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')

# Create Content Governance table
def create_governance_table():
    try:
        response = dynamodb.create_table(
            TableName='hcg-demo-content-governance',
            KeySchema=[
                {'AttributeName': 'document_id', 'KeyType': 'HASH'},
                {'AttributeName': 'version', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'document_id', 'AttributeType': 'S'},
                {'AttributeName': 'version', 'AttributeType': 'N'},
                {'AttributeName': 'zone', 'AttributeType': 'S'},
                {'AttributeName': 'review_date', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'zone-index',
                    'KeySchema': [{'AttributeName': 'zone', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'review-date-index',
                    'KeySchema': [{'AttributeName': 'review_date', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✅ Created table: hcg-demo-content-governance")
        return response['TableDescription']['TableArn']
    except dynamodb.exceptions.ResourceInUseException:
        print("✅ Table already exists: hcg-demo-content-governance")
        return None

# Create Document Owners table
def create_owners_table():
    try:
        response = dynamodb.create_table(
            TableName='hcg-demo-document-owners',
            KeySchema=[
                {'AttributeName': 'domain', 'KeyType': 'HASH'},
                {'AttributeName': 'document_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'domain', 'AttributeType': 'S'},
                {'AttributeName': 'document_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✅ Created table: hcg-demo-document-owners")
        return response['TableDescription']['TableArn']
    except dynamodb.exceptions.ResourceInUseException:
        print("✅ Table already exists: hcg-demo-document-owners")
        return None

if __name__ == '__main__':
    print("Creating Content Governance tables...")
    governance_arn = create_governance_table()
    owners_arn = create_owners_table()
    print("\n✅ Content Governance schema created successfully")
