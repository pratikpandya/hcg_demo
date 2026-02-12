import json

# Confidence thresholds
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_MEDIUM = 0.6
CONFIDENCE_THRESHOLD_LOW = 0.4

def calculate_kb_confidence(retrieved_references):
    """Calculate confidence score from KB retrieval"""
    if not retrieved_references:
        return 0.0
    
    # Average confidence from retrieval scores
    scores = []
    for ref in retrieved_references:
        score = ref.get('metadata', {}).get('score', 0.5)
        scores.append(score)
    
    if not scores:
        return 0.5
    
    avg_score = sum(scores) / len(scores)
    
    # Boost if multiple sources agree
    if len(scores) >= 3:
        avg_score = min(avg_score + 0.1, 1.0)
    
    return avg_score

def should_respond(confidence, query_classification_confidence):
    """Determine if agent should respond or fallback"""
    # Combine KB confidence with query classification confidence
    combined_confidence = (confidence + query_classification_confidence) / 2
    
    if combined_confidence >= CONFIDENCE_THRESHOLD_HIGH:
        return True, "high"
    elif combined_confidence >= CONFIDENCE_THRESHOLD_MEDIUM:
        return True, "medium"
    elif combined_confidence >= CONFIDENCE_THRESHOLD_LOW:
        return True, "low"
    else:
        return False, "insufficient"

def get_fallback_response(query, domain):
    """Generate safe fallback response"""
    fallback_responses = {
        'hr': "I don't have enough information to answer that HR question confidently. Please contact HR directly at hr@starhub.com or extension 2100.",
        'it': "I'm not certain about that IT question. Please contact IT Support at itsupport@starhub.com or +65 6825 3000 for accurate assistance.",
        'finance': "I don't have sufficient information about that finance query. Please reach out to the Finance team at finance@starhub.com or extension 2200.",
        'general': "I'm not confident I can answer that accurately. Please contact the relevant department or check the company intranet for verified information."
    }
    
    return fallback_responses.get(domain, fallback_responses['general'])

def add_confidence_disclaimer(response, confidence_level):
    """Add disclaimer for medium/low confidence responses"""
    if confidence_level == "medium":
        return f"{response}\n\n_Note: This information may not be complete. Please verify with the relevant department._"
    elif confidence_level == "low":
        return f"{response}\n\n_⚠️ Low confidence: Please verify this information with the relevant department before taking action._"
    else:
        return response

def detect_pii(text):
    """Basic PII detection (enhanced by Bedrock Guardrails)"""
    import re
    
    pii_patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{4}[-.\s]?\d{4}\b|\b\+65[-.\s]?\d{4}[-.\s]?\d{4}\b',
        'nric': r'\b[STFG]\d{7}[A-Z]\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    }
    
    detected = []
    for pii_type, pattern in pii_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            detected.append(pii_type)
    
    return detected

def sanitize_response(response):
    """Remove potential PII from response"""
    import re
    
    # Redact email addresses
    response = re.sub(
        r'\b[A-Za-z0-9._%+-]+@(?!starhub\.com)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL REDACTED]',
        response,
        flags=re.IGNORECASE
    )
    
    # Redact phone numbers (except official StarHub numbers)
    response = re.sub(
        r'\b(?!\+65\s?6825)\d{4}[-.\s]?\d{4}\b',
        '[PHONE REDACTED]',
        response
    )
    
    # Redact NRIC
    response = re.sub(
        r'\b[STFG]\d{7}[A-Z]\b',
        '[NRIC REDACTED]',
        response
    )
    
    return response

def check_hallucination_indicators(response, citations):
    """Check for potential hallucination"""
    hallucination_score = 0.0
    
    # No citations = potential hallucination
    if not citations or len(citations) == 0:
        hallucination_score += 0.5
    
    # Very short response with no citations
    if len(response.split()) < 10 and not citations:
        hallucination_score += 0.3
    
    # Contains phrases indicating uncertainty
    uncertain_phrases = [
        "i think", "maybe", "probably", "i'm not sure",
        "it might be", "could be", "possibly"
    ]
    
    response_lower = response.lower()
    for phrase in uncertain_phrases:
        if phrase in response_lower:
            hallucination_score += 0.1
    
    # Contains specific numbers/dates without citations
    import re
    has_numbers = bool(re.search(r'\d+', response))
    if has_numbers and not citations:
        hallucination_score += 0.2
    
    return min(hallucination_score, 1.0)

def validate_response(response, citations, query_confidence, domain):
    """Comprehensive response validation"""
    
    # Calculate KB confidence
    kb_confidence = calculate_kb_confidence(citations)
    
    # Check if should respond
    should_answer, confidence_level = should_respond(kb_confidence, query_confidence)
    
    if not should_answer:
        return {
            'safe_to_respond': False,
            'response': get_fallback_response("", domain),
            'confidence': kb_confidence,
            'confidence_level': confidence_level,
            'reason': 'Low confidence'
        }
    
    # Check for hallucination
    hallucination_score = check_hallucination_indicators(response, citations)
    
    if hallucination_score > 0.7:
        return {
            'safe_to_respond': False,
            'response': get_fallback_response("", domain),
            'confidence': kb_confidence,
            'confidence_level': 'insufficient',
            'reason': 'High hallucination risk'
        }
    
    # Detect PII in query
    pii_detected = detect_pii(response)
    
    if pii_detected:
        response = sanitize_response(response)
    
    # Add disclaimer if needed
    response = add_confidence_disclaimer(response, confidence_level)
    
    return {
        'safe_to_respond': True,
        'response': response,
        'confidence': kb_confidence,
        'confidence_level': confidence_level,
        'pii_detected': pii_detected,
        'hallucination_score': hallucination_score
    }
