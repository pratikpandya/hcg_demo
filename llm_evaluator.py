import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-southeast-1')

def evaluate_faithfulness(query, response, citations):
    """Evaluate if response is faithful to source documents"""
    
    prompt = f"""Evaluate if the following response is faithful to the provided sources.

Query: {query}

Response: {response}

Sources:
{chr(10).join([f"- {c.get('content', '')[:200]}" for c in citations[:3]])}

Rate faithfulness from 0-10 where:
- 10: Response is fully supported by sources
- 5: Response is partially supported
- 0: Response contradicts or has no support from sources

Respond with ONLY a number 0-10."""

    try:
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        score_text = result['content'][0]['text'].strip()
        score = float(score_text)
        return min(max(score / 10.0, 0.0), 1.0)
    except:
        return 0.5

def evaluate_relevancy(query, response):
    """Evaluate if response is relevant to query"""
    
    prompt = f"""Evaluate if the following response is relevant to the query.

Query: {query}

Response: {response}

Rate relevancy from 0-10 where:
- 10: Response directly answers the query
- 5: Response is somewhat related
- 0: Response is completely irrelevant

Respond with ONLY a number 0-10."""

    try:
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        score_text = result['content'][0]['text'].strip()
        score = float(score_text)
        return min(max(score / 10.0, 0.0), 1.0)
    except:
        return 0.5

def evaluate_completeness(query, response):
    """Evaluate if response is complete"""
    
    prompt = f"""Evaluate if the following response completely answers the query.

Query: {query}

Response: {response}

Rate completeness from 0-10 where:
- 10: Response fully answers all aspects of the query
- 5: Response partially answers the query
- 0: Response doesn't answer the query

Respond with ONLY a number 0-10."""

    try:
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        score_text = result['content'][0]['text'].strip()
        score = float(score_text)
        return min(max(score / 10.0, 0.0), 1.0)
    except:
        return 0.5

def evaluate_response(query, response, citations, domain, expected_domain=None):
    """Comprehensive response evaluation"""
    
    # Routing accuracy
    routing_accuracy = 1.0 if expected_domain and domain == expected_domain else 0.0
    
    # LLM-as-judge metrics
    faithfulness = evaluate_faithfulness(query, response, citations)
    relevancy = evaluate_relevancy(query, response)
    completeness = evaluate_completeness(query, response)
    
    # Citation quality
    citation_score = min(len(citations) / 3.0, 1.0)
    
    # Overall quality
    overall_quality = (faithfulness * 0.4 + relevancy * 0.3 + completeness * 0.2 + citation_score * 0.1)
    
    return {
        'routing_accuracy': routing_accuracy,
        'faithfulness': faithfulness,
        'relevancy': relevancy,
        'completeness': completeness,
        'citation_score': citation_score,
        'overall_quality': overall_quality,
        'metrics': {
            'faithfulness': f"{faithfulness:.2f}",
            'relevancy': f"{relevancy:.2f}",
            'completeness': f"{completeness:.2f}",
            'citations': len(citations),
            'overall': f"{overall_quality:.2f}"
        }
    }

def log_evaluation_metrics(evaluation, cloudwatch_client):
    """Log evaluation metrics to CloudWatch"""
    
    try:
        cloudwatch_client.put_metric_data(
            Namespace='HCG-Demo',
            MetricData=[
                {'MetricName': 'Faithfulness', 'Value': evaluation['faithfulness'], 'Unit': 'None'},
                {'MetricName': 'Relevancy', 'Value': evaluation['relevancy'], 'Unit': 'None'},
                {'MetricName': 'Completeness', 'Value': evaluation['completeness'], 'Unit': 'None'},
                {'MetricName': 'OverallQuality', 'Value': evaluation['overall_quality'], 'Unit': 'None'},
                {'MetricName': 'RoutingAccuracy', 'Value': evaluation['routing_accuracy'], 'Unit': 'None'}
            ]
        )
    except Exception as e:
        print(f"Error logging metrics: {e}")
