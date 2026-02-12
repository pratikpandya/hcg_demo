import json
import boto3
from datetime import datetime
from urllib import request, error

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
cloudwatch = boto3.client('cloudwatch', region_name='ap-southeast-1')

catalog_table = dynamodb.Table('hcg-demo-resource-catalog')
health_table = dynamodb.Table('hcg-demo-link-health')

def lambda_handler(event, context):
    resource_id = event.get('resource_id')
    
    if resource_id:
        result = check_single_resource(resource_id)
        return {'statusCode': 200, 'body': json.dumps(result)}
    else:
        results = check_all_resources()
        return {'statusCode': 200, 'body': json.dumps(results)}

def check_all_resources():
    response = catalog_table.scan()
    resources = response['Items']
    
    results = {
        'total': len(resources),
        'healthy': 0,
        'unhealthy': 0,
        'checks': []
    }
    
    for resource in resources:
        check_result = check_single_resource(resource['resource_id'])
        results['checks'].append(check_result)
        
        if check_result['status'] == 'healthy':
            results['healthy'] += 1
        else:
            results['unhealthy'] += 1
    
    # Publish CloudWatch metrics
    cloudwatch.put_metric_data(
        Namespace='HCG-Demo/DeepLinking',
        MetricData=[
            {
                'MetricName': 'HealthyLinks',
                'Value': results['healthy'],
                'Unit': 'Count',
                'Timestamp': datetime.now()
            },
            {
                'MetricName': 'UnhealthyLinks',
                'Value': results['unhealthy'],
                'Unit': 'Count',
                'Timestamp': datetime.now()
            }
        ]
    )
    
    return results

def check_single_resource(resource_id):
    # Get resource from catalog
    response = catalog_table.get_item(Key={'resource_id': resource_id})
    
    if 'Item' not in response:
        return {'resource_id': resource_id, 'status': 'not_found'}
    
    resource = response['Item']
    base_url = resource['base_url']
    
    # Perform health check
    health_status = validate_url(base_url)
    
    # Store health check result
    timestamp = datetime.now().isoformat()
    health_table.put_item(Item={
        'resource_id': resource_id,
        'check_timestamp': timestamp,
        'status': health_status['status'],
        'response_time_ms': health_status['response_time'],
        'status_code': health_status.get('status_code'),
        'error': health_status.get('error')
    })
    
    # Update catalog with last validation
    catalog_table.update_item(
        Key={'resource_id': resource_id},
        UpdateExpression='SET last_validated = :timestamp, #status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':timestamp': timestamp,
            ':status': 'active' if health_status['status'] == 'healthy' else 'degraded'
        }
    )
    
    return {
        'resource_id': resource_id,
        'resource_name': resource['name'],
        'status': health_status['status'],
        'response_time_ms': health_status['response_time'],
        'checked_at': timestamp
    }

def validate_url(url):
    start_time = datetime.now()
    
    try:
        req = request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'HCG-LinkHealthCheck/1.0')
        
        with request.urlopen(req, timeout=5) as response:
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'status': 'healthy',
                'status_code': response.status,
                'response_time': response_time
            }
    
    except error.HTTPError as e:
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        return {
            'status': 'unhealthy',
            'status_code': e.code,
            'response_time': response_time,
            'error': str(e)
        }
    
    except Exception as e:
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        return {
            'status': 'unhealthy',
            'response_time': response_time,
            'error': str(e)
        }
