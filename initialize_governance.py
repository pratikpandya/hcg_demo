import boto3
import json
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
governance_table = dynamodb.Table('hcg-demo-content-governance')
owners_table = dynamodb.Table('hcg-demo-document-owners')

# Initial document assignments
INITIAL_DOCUMENTS = {
    'hr': [
        {'id': 'hr-leave-policy', 'title': 'Leave Policy', 'zone': 'GREEN'},
        {'id': 'hr-benefits-guide', 'title': 'Benefits Guide', 'zone': 'GREEN'}
    ],
    'it': [
        {'id': 'it-laptop-setup', 'title': 'Laptop Setup Guide', 'zone': 'GREEN'},
        {'id': 'it-vpn-access', 'title': 'VPN Access Guide', 'zone': 'GREEN'},
        {'id': 'it-security-policy', 'title': 'Security Policy', 'zone': 'GREEN'}
    ],
    'finance': [
        {'id': 'finance-expense-policy', 'title': 'Expense Policy', 'zone': 'GREEN'},
        {'id': 'finance-reimbursement', 'title': 'Reimbursement Guide', 'zone': 'GREEN'}
    ],
    'general': [
        {'id': 'general-company-handbook', 'title': 'Company Handbook', 'zone': 'GREEN'},
        {'id': 'general-code-of-conduct', 'title': 'Code of Conduct', 'zone': 'GREEN'},
        {'id': 'general-office-guide', 'title': 'Office Guide', 'zone': 'GREEN'}
    ]
}

DOMAIN_OWNERS = {
    'hr': {'owner': 'hr-team@company.com', 'approver': 'hr-director@company.com'},
    'it': {'owner': 'it-team@company.com', 'approver': 'it-director@company.com'},
    'finance': {'owner': 'finance-team@company.com', 'approver': 'cfo@company.com'},
    'general': {'owner': 'admin-team@company.com', 'approver': 'admin-director@company.com'}
}

ZONE_REVIEW_DAYS = {
    'GREEN': 90,
    'YELLOW': 30,
    'RED': 0
}

def initialize_governance():
    print("Initializing content governance for existing documents...")
    
    for domain, documents in INITIAL_DOCUMENTS.items():
        print(f"\n📁 Processing {domain.upper()} domain...")
        
        for doc in documents:
            doc_id = doc['id']
            zone = doc['zone']
            version = int(datetime.now().timestamp())
            review_date = (datetime.now() + timedelta(days=ZONE_REVIEW_DAYS[zone])).isoformat()
            
            # Create governance record
            governance_table.put_item(Item={
                'document_id': doc_id,
                'version': version,
                'domain': domain,
                'zone': zone,
                'title': doc['title'],
                'approver': 'system-migration',
                'approved_at': datetime.now().isoformat(),
                'review_date': review_date,
                'status': 'APPROVED'
            })
            
            # Assign owner
            owners_table.put_item(Item={
                'domain': domain,
                'document_id': doc_id,
                'owner': DOMAIN_OWNERS[domain]['owner'],
                'approver': DOMAIN_OWNERS[domain]['approver'],
                'assigned_at': datetime.now().isoformat()
            })
            
            print(f"  ✅ {doc_id} → {zone} zone (Review: {review_date[:10]})")
    
    print("\n✅ Content governance initialized successfully")
    
    # Summary
    total_docs = sum(len(docs) for docs in INITIAL_DOCUMENTS.values())
    print(f"\nSummary:")
    print(f"  - Total documents: {total_docs}")
    print(f"  - GREEN zone: {total_docs} (all approved)")
    print(f"  - Domains: {len(INITIAL_DOCUMENTS)}")
    print(f"  - Next review: {(datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    initialize_governance()
