import json

# Validation dataset for routing accuracy and quality testing
validation_dataset = {
    "hr_queries": [
        {"query": "How many days of annual leave do I get?", "expected_domain": "hr", "expected_answer_contains": ["14", "21", "annual leave"]},
        {"query": "What is the maternity leave policy?", "expected_domain": "hr", "expected_answer_contains": ["16 weeks", "maternity"]},
        {"query": "How do I apply for leave?", "expected_domain": "hr", "expected_answer_contains": ["HR portal", "2 weeks"]},
        {"query": "What benefits do employees get?", "expected_domain": "hr", "expected_answer_contains": ["medical", "insurance", "bonus"]},
        {"query": "What is the medical leave entitlement?", "expected_domain": "hr", "expected_answer_contains": ["14 days", "medical"]},
        {"query": "Can I carry forward unused leave?", "expected_domain": "hr", "expected_answer_contains": ["7 days", "carry forward"]},
        {"query": "What is paternity leave?", "expected_domain": "hr", "expected_answer_contains": ["2 weeks", "paternity"]},
        {"query": "How do I contact HR?", "expected_domain": "hr", "expected_answer_contains": ["hr@starhub.com", "2100"]},
        {"query": "What is the onboarding process?", "expected_domain": "hr", "expected_answer_contains": ["orientation", "Day 1"]},
        {"query": "What insurance coverage do we have?", "expected_domain": "hr", "expected_answer_contains": ["medical", "life insurance"]}
    ],
    "it_queries": [
        {"query": "How do I reset my password?", "expected_domain": "it", "expected_answer_contains": ["password.starhub.com", "self-service"]},
        {"query": "My laptop is not working", "expected_domain": "it", "expected_answer_contains": ["IT Support", "6825 3000"]},
        {"query": "How do I connect to VPN?", "expected_domain": "it", "expected_answer_contains": ["Cisco AnyConnect", "vpn.starhub.com"]},
        {"query": "How do I install software?", "expected_domain": "it", "expected_answer_contains": ["Software Center", "IT portal"]},
        {"query": "My account is locked", "expected_domain": "it", "expected_answer_contains": ["30 minutes", "unlock"]},
        {"query": "How do I set up MFA?", "expected_domain": "it", "expected_answer_contains": ["Microsoft Authenticator", "QR code"]},
        {"query": "VPN is not connecting", "expected_domain": "it", "expected_answer_contains": ["vpn.starhub.com", "IT Support"]},
        {"query": "How do I troubleshoot my laptop?", "expected_domain": "it", "expected_answer_contains": ["restart", "IT Support"]},
        {"query": "What is the IT helpdesk number?", "expected_domain": "it", "expected_answer_contains": ["6825 3000", "itsupport@starhub.com"]},
        {"query": "How do I request new software?", "expected_domain": "it", "expected_answer_contains": ["IT portal", "manager approval"]}
    ],
    "finance_queries": [
        {"query": "How do I claim expenses?", "expected_domain": "finance", "expected_answer_contains": ["Finance portal", "receipt"]},
        {"query": "What is the expense reimbursement policy?", "expected_domain": "finance", "expected_answer_contains": ["30 days", "receipt"]},
        {"query": "What is the procurement process?", "expected_domain": "finance", "expected_answer_contains": ["quotations", "approval"]},
        {"query": "How long does reimbursement take?", "expected_domain": "finance", "expected_answer_contains": ["7 business days", "approval"]},
        {"query": "What are the meal expense limits?", "expected_domain": "finance", "expected_answer_contains": ["lunch", "dinner", "$"]},
        {"query": "How do I submit an expense claim?", "expected_domain": "finance", "expected_answer_contains": ["Finance portal", "upload receipt"]},
        {"query": "What is the procurement authority?", "expected_domain": "finance", "expected_answer_contains": ["$1,000", "manager"]},
        {"query": "Can I claim taxi expenses?", "expected_domain": "finance", "expected_answer_contains": ["taxi", "receipt"]},
        {"query": "How do I contact finance?", "expected_domain": "finance", "expected_answer_contains": ["finance@starhub.com", "2200"]},
        {"query": "What expenses are reimbursable?", "expected_domain": "finance", "expected_answer_contains": ["travel", "meals", "business"]}
    ],
    "general_queries": [
        {"query": "Where is the office located?", "expected_domain": "general", "expected_answer_contains": ["Cuppage Road", "Singapore"]},
        {"query": "What are the office hours?", "expected_domain": "general", "expected_answer_contains": ["9:00 AM", "6:00 PM"]},
        {"query": "Can I work from home?", "expected_domain": "general", "expected_answer_contains": ["3 days", "manager"]},
        {"query": "What is the dress code?", "expected_domain": "general", "expected_answer_contains": ["business casual", "Friday"]},
        {"query": "How do I get to the office?", "expected_domain": "general", "expected_answer_contains": ["MRT", "Orchard"]},
        {"query": "What are the company policies?", "expected_domain": "general", "expected_answer_contains": ["policy", "HR"]},
        {"query": "Where can I park?", "expected_domain": "general", "expected_answer_contains": ["parking", "basement"]},
        {"query": "What is the company address?", "expected_domain": "general", "expected_answer_contains": ["51 Cuppage Road", "229469"]},
        {"query": "Are there customer service centers?", "expected_domain": "general", "expected_answer_contains": ["Orchard", "Jurong", "Tampines"]},
        {"query": "What is the general enquiry number?", "expected_domain": "general", "expected_answer_contains": ["1633", "6825 0000"]}
    ]
}

# Save dataset
with open('validation_dataset.json', 'w') as f:
    json.dump(validation_dataset, f, indent=2)

# Generate statistics
total_queries = sum(len(queries) for queries in validation_dataset.values())

print("="*70)
print("📋 Validation Dataset Created")
print("="*70)
print(f"\nTotal Queries: {total_queries}")
print(f"\nBreakdown:")
for domain, queries in validation_dataset.items():
    print(f"  {domain.replace('_queries', '').upper()}: {len(queries)} queries")

print(f"\n✅ Dataset saved to: validation_dataset.json")
print("\nDataset can be used for:")
print("  - Routing accuracy testing")
print("  - Response quality evaluation")
print("  - Regression testing")
print("  - Performance benchmarking")
