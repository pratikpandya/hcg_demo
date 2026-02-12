import json
import boto3
import time
import os

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
secrets_client = boto3.client('secretsmanager', region_name='ap-southeast-1')

sessions_table = dynamodb.Table('hcg-demo-sessions')
feedback_table = dynamodb.Table('hcg-demo-feedback')

def get_slack_token():
    """Get Slack token from Secrets Manager"""
    response = secrets_client.get_secret_value(SecretId='hcg-demo/slack/credentials')
    secret = json.loads(response['SecretString'])
    return secret['bot_token']

def post_slack_message(channel, text, thread_ts=None, blocks=None):
    """Post message to Slack"""
    import urllib.request
    import urllib.parse
    
    token = get_slack_token()
    
    payload = {
        'channel': channel,
        'text': text,
        'thread_ts': thread_ts
    }
    
    if blocks:
        payload['blocks'] = blocks
    
    req = urllib.request.Request(
        'https://slack.com/api/chat.postMessage',
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def update_slack_message(channel, ts, text, blocks=None):
    """Update existing Slack message"""
    import urllib.request
    
    token = get_slack_token()
    
    payload = {
        'channel': channel,
        'ts': ts,
        'text': text
    }
    
    if blocks:
        payload['blocks'] = blocks
    
    req = urllib.request.Request(
        'https://slack.com/api/chat.update',
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def format_response_with_citations(response_text, citations, domain):
    """Format response with Slack Block Kit"""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": response_text
            }
        }
    ]
    
    # Add citations
    if citations:
        citation_text = "*Sources:*\n"
        for i, cite in enumerate(citations[:3], 1):
            content = cite.get('content', '')[:100]
            location = cite.get('location', 'Unknown')
            citation_text += f"{i}. {content}... _({location})_\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": citation_text
            }
        })
    
    # Add follow-up suggestions
    follow_ups = get_follow_up_suggestions(domain)
    if follow_ups:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": suggestion},
                    "value": suggestion,
                    "action_id": f"followup_{i}"
                }
                for i, suggestion in enumerate(follow_ups[:3])
            ]
        })
    
    # Add feedback buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "emoji": True, "text": "👍 Helpful"},
                "value": "helpful",
                "action_id": "feedback_helpful"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "emoji": True, "text": "👎 Not Helpful"},
                "value": "not_helpful",
                "action_id": "feedback_not_helpful"
            }
        ]
    })
    
    return blocks

def get_follow_up_suggestions(domain):
    """Get domain-specific follow-up suggestions"""
    suggestions = {
        'hr': ["View leave policy", "Check benefits", "Contact HR"],
        'it': ["Create IT ticket", "Check VPN guide", "Password reset"],
        'finance': ["View expense policy", "Submit claim", "Contact finance"],
        'general': ["Office locations", "Company policies", "Contact info"]
    }
    return suggestions.get(domain, ["Ask another question"])

def invoke_supervisor(query, session_id):
    """Invoke supervisor orchestrator"""
    response = lambda_client.invoke(
        FunctionName='hcg-demo-supervisor-orchestrator',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'body': json.dumps({
                'query': query,
                'session_id': session_id
            })
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    if result['statusCode'] == 200:
        return json.loads(result['body'])
    else:
        return {'error': 'Failed to get response'}

def lambda_handler(event, context):
    """Slack webhook handler with UX features"""
    
    body = json.loads(event['body'])
    
    # Handle URL verification
    if body.get('type') == 'url_verification':
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': body['challenge']})
        }
    
    # Handle interactive actions (button clicks)
    if body.get('type') == 'block_actions':
        payload = body
        user_id = payload['user']['id']
        action = payload['actions'][0]
        action_id = action['action_id']
        
        # Handle feedback
        if action_id.startswith('feedback_'):
            feedback_type = action['value']
            
            feedback_table.put_item(Item={
                'feedbackId': f"{user_id}_{int(time.time())}",
                'userId': user_id,
                'feedback': feedback_type,
                'timestamp': int(time.time())
            })
            
            return {
                'statusCode': 200,
                'body': json.dumps({'text': 'Thanks for your feedback!'})
            }
        
        # Handle follow-up
        if action_id.startswith('followup_'):
            # Treat as new query
            channel_id = payload['channel']['id']
            thread_ts = payload['message']['ts']
            query = action['value']
            
            # Post thinking message
            thinking_msg = post_slack_message(
                channel_id,
                "🤔 Thinking...",
                thread_ts
            )
            
            # Invoke agent
            session_id = f"{channel_id}_{thread_ts}"
            result = invoke_supervisor(query, session_id)
            
            if 'error' not in result:
                blocks = format_response_with_citations(
                    result['response'],
                    result.get('citations', []),
                    result.get('domain', 'general')
                )
                
                update_slack_message(
                    channel_id,
                    thinking_msg['ts'],
                    result['response'],
                    blocks
                )
            
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
    
    # Handle message events
    if body.get('type') == 'event_callback':
        slack_event = body['event']
        
        # Ignore bot messages
        if slack_event.get('bot_id'):
            return {'statusCode': 200, 'body': json.dumps({'ok': True})}
        
        user_id = slack_event.get('user')
        channel_id = slack_event.get('channel')
        text = slack_event.get('text', '')
        thread_ts = slack_event.get('thread_ts', slack_event.get('ts'))
        
        # Store session
        session_id = f"{channel_id}_{thread_ts}"
        sessions_table.put_item(Item={
            'sessionId': session_id,
            'userId': user_id,
            'query': text,
            'timestamp': int(time.time()),
            'ttl': int(time.time()) + 28800
        })
        
        # Post progressive status
        status_msg = post_slack_message(
            channel_id,
            "🤔 Thinking...",
            thread_ts
        )
        
        time.sleep(1)
        update_slack_message(
            channel_id,
            status_msg['ts'],
            "🔍 Searching knowledge base..."
        )
        
        # Invoke supervisor
        result = invoke_supervisor(text, session_id)
        
        if 'error' not in result:
            # Format with Block Kit
            blocks = format_response_with_citations(
                result['response'],
                result.get('citations', []),
                result.get('domain', 'general')
            )
            
            update_slack_message(
                channel_id,
                status_msg['ts'],
                result['response'],
                blocks
            )
        else:
            update_slack_message(
                channel_id,
                status_msg['ts'],
                "Sorry, I encountered an error. Please try again."
            )
        
        return {'statusCode': 200, 'body': json.dumps({'ok': True})}
    
    return {'statusCode': 200, 'body': json.dumps({'ok': True})}
