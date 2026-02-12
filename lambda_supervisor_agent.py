import json
import boto3
import re

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-1')

# Import safe failure handler
import sys
sys.path.append('/opt/python')

try:
    from safe_failure_handler import (
        validate_response,
        calculate_kb_confidence,
        get_fallback_response
    )
except ImportError:
    # Inline minimal version if import fails
    def validate_response(response, citations, query_confidence, domain):
        kb_confidence = len(citations) / 5.0 if citations else 0.0
        combined = (kb_confidence + query_confidence) / 2
        
        if combined < 0.6:
            return {
                'safe_to_respond': False,
                'response': f"I don't have enough information to answer that confidently. Please contact the {domain.upper()} team directly.",
                'confidence': combined,
                'confidence_level': 'low'
            }
        
        return {
            'safe_to_respond': True,
            'response': response,
            'confidence': combined,
            'confidence_level': 'high' if combined > 0.8 else 'medium'
        }

# Agent configurations
AGENTS = {
    'hr': {'id': 'IEVMSZT1GY', 'alias': 'VFYW9OV9IU'},
    'it': {'id': 'ZMLHZEZZXO', 'alias': 'BFBSNUNZUA'},
    'finance': {'id': '8H5G4JZVXM', 'alias': '1ZFUCWCS1K'},
    'general': {'id': 'RY3QRSI7VE', 'alias': '9CP8PGSKFQ'}
}

def classify_query(query):
    """Classify user query to appropriate domain"""
    query_lower = query.lower()
    
    # HR keywords
    hr_keywords = ['leave', 'vacation', 'maternity', 'paternity', 'benefit', 'insurance', 'medical', 'salary', 'bonus', 'hr', 'employee', 'onboarding']
    if any(kw in query_lower for kw in hr_keywords):
        return 'hr', 0.9
    
    # IT keywords
    it_keywords = ['password', 'laptop', 'vpn', 'software', 'install', 'computer', 'network', 'login', 'access', 'it support', 'troubleshoot']
    if any(kw in query_lower for kw in it_keywords):
        return 'it', 0.9
    
    # Finance keywords
    finance_keywords = ['expense', 'reimbursement', 'procurement', 'purchase', 'invoice', 'payment', 'budget', 'finance', 'cost']
    if any(kw in query_lower for kw in finance_keywords):
        return 'finance', 0.9
    
    # Default to general
    return 'general', 0.7

def invoke_agent(agent_id, query, session_id, alias_id='TSTALIASID'):
    """Invoke specialist agent"""
    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=query
        )
        
        # Extract response
        completion = ""
        citations = []
        
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
            
            if 'trace' in event:
                trace = event['trace'].get('trace', {})
                if 'orchestrationTrace' in trace:
                    orch = trace['orchestrationTrace']
                    if 'observation' in orch:
                        obs = orch['observation']
                        if 'knowledgeBaseLookupOutput' in obs:
                            kb_output = obs['knowledgeBaseLookupOutput']
                            if 'retrievedReferences' in kb_output:
                                citations.extend(kb_output['retrievedReferences'])
        
        return {
            'response': completion,
            'citations': citations,
            'confidence': 0.9
        }
        
    except Exception as e:
        return {
            'response': f"Error invoking agent: {str(e)}",
            'citations': [],
            'confidence': 0.0
        }

def lambda_handler(event, context):
    """Supervisor agent - routes queries to specialists"""
    
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '')
        session_id = body.get('session_id', 'default-session')
        
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Query is required'})
            }
        
        # Classify query
        domain, confidence = classify_query(query)
        agent_config = AGENTS[domain]
        agent_id = agent_config['id']
        alias_id = agent_config['alias']
        
        # Invoke specialist agent
        result = invoke_agent(agent_id, query, session_id, alias_id)
        
        # Validate response with safe failure handling
        validation = validate_response(
            result['response'],
            result['citations'],
            confidence,
            domain
        )
        
        # Format response with validation results
        response_data = {
            'query': query,
            'domain': domain,
            'agent_id': agent_id,
            'confidence': validation['confidence'],
            'confidence_level': validation['confidence_level'],
            'safe_to_respond': validation['safe_to_respond'],
            'response': validation['response'],
            'citations': [
                {
                    'content': c.get('content', {}).get('text', ''),
                    'location': c.get('location', {}).get('s3Location', {}).get('uri', '')
                }
                for c in result['citations']
            ] if validation['safe_to_respond'] else []
        }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
