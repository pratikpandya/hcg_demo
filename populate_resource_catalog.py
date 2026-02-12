import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
catalog_table = dynamodb.Table('hcg-demo-resource-catalog')

# Resource catalog with SSO-enabled deep links
RESOURCE_CATALOG = [
    # HR Systems
    {
        'resource_id': 'workday',
        'name': 'Workday',
        'category': 'hr_system',
        'domain': 'hr',
        'base_url': 'https://company.workday.com',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'leave_request': '/leave/request',
            'timesheet': '/time/entry',
            'benefits': '/benefits/enrollment',
            'payslip': '/payroll/payslip'
        },
        'keywords': ['leave', 'timesheet', 'benefits', 'payslip', 'workday'],
        'contact': 'hr-support@company.com'
    },
    {
        'resource_id': 'hubbahub',
        'name': 'HubbaHub',
        'category': 'hr_portal',
        'domain': 'hr',
        'base_url': 'https://hubbahub.company.com',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'policies': '/policies',
            'org_chart': '/organization',
            'directory': '/directory',
            'announcements': '/news'
        },
        'keywords': ['policies', 'org chart', 'directory', 'employee', 'hubbahub'],
        'contact': 'hr-support@company.com'
    },
    # IT Systems
    {
        'resource_id': 'servicenow',
        'name': 'ServiceNow',
        'category': 'it_system',
        'domain': 'it',
        'base_url': 'https://company.service-now.com',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'create_incident': '/nav_to.do?uri=incident.do',
            'my_incidents': '/nav_to.do?uri=incident_list.do',
            'catalog': '/nav_to.do?uri=sc_catalog.do',
            'kb': '/nav_to.do?uri=kb_view.do'
        },
        'keywords': ['incident', 'ticket', 'it support', 'servicenow', 'service request'],
        'contact': 'it-support@company.com'
    },
    {
        'resource_id': 'vpn',
        'name': 'VPN Portal',
        'category': 'it_portal',
        'domain': 'it',
        'base_url': 'https://vpn.company.com',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'connect': '/connect',
            'download': '/download',
            'troubleshoot': '/help'
        },
        'keywords': ['vpn', 'remote access', 'network'],
        'contact': 'it-support@company.com'
    },
    {
        'resource_id': 'okta',
        'name': 'Okta SSO',
        'category': 'it_system',
        'domain': 'it',
        'base_url': 'https://company.okta.com',
        'sso_enabled': False,
        'sso_provider': None,
        'deep_links': {
            'dashboard': '/app/UserHome',
            'profile': '/enduser/settings',
            'mfa': '/enduser/settings/mfa'
        },
        'keywords': ['sso', 'login', 'password', 'mfa', 'okta'],
        'contact': 'it-support@company.com'
    },
    # Finance Systems
    {
        'resource_id': 'concur',
        'name': 'Concur',
        'category': 'finance_system',
        'domain': 'finance',
        'base_url': 'https://company.concursolutions.com',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'expense_report': '/expense/create',
            'travel_request': '/travel/request',
            'receipts': '/receipts/upload',
            'approvals': '/approvals/pending'
        },
        'keywords': ['expense', 'reimbursement', 'travel', 'concur', 'receipt'],
        'contact': 'finance-support@company.com'
    },
    {
        'resource_id': 'sap',
        'name': 'SAP',
        'category': 'finance_system',
        'domain': 'finance',
        'base_url': 'https://sap.company.com',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'purchase_order': '/po/create',
            'invoice': '/invoice/view',
            'vendor': '/vendor/manage'
        },
        'keywords': ['purchase order', 'invoice', 'vendor', 'sap', 'procurement'],
        'contact': 'finance-support@company.com'
    },
    # General Systems
    {
        'resource_id': 'sharepoint',
        'name': 'SharePoint',
        'category': 'collaboration',
        'domain': 'general',
        'base_url': 'https://company.sharepoint.com',
        'sso_enabled': True,
        'sso_provider': 'azure_ad',
        'deep_links': {
            'documents': '/sites/HCG/Documents',
            'policies': '/sites/HCG/Policies',
            'templates': '/sites/HCG/Templates'
        },
        'keywords': ['documents', 'sharepoint', 'files', 'policies'],
        'contact': 'admin-support@company.com'
    },
    {
        'resource_id': 'confluence',
        'name': 'Confluence',
        'category': 'collaboration',
        'domain': 'general',
        'base_url': 'https://company.atlassian.net/wiki',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'home': '/spaces',
            'search': '/search',
            'recent': '/recent'
        },
        'keywords': ['wiki', 'confluence', 'documentation', 'knowledge base'],
        'contact': 'admin-support@company.com'
    },
    {
        'resource_id': 'slack',
        'name': 'Slack',
        'category': 'collaboration',
        'domain': 'general',
        'base_url': 'https://company.slack.com',
        'sso_enabled': True,
        'sso_provider': 'okta',
        'deep_links': {
            'channel': '/archives',
            'dm': '/messages',
            'search': '/search'
        },
        'keywords': ['slack', 'chat', 'message', 'channel'],
        'contact': 'admin-support@company.com'
    }
]

def populate_catalog():
    print("Populating resource catalog...")
    
    for resource in RESOURCE_CATALOG:
        resource['created_at'] = datetime.now().isoformat()
        resource['status'] = 'active'
        resource['last_validated'] = datetime.now().isoformat()
        
        catalog_table.put_item(Item=resource)
        print(f"  ✅ {resource['name']} ({resource['category']})")
    
    print(f"\n✅ Populated {len(RESOURCE_CATALOG)} resources")
    
    # Summary by category
    categories = {}
    for r in RESOURCE_CATALOG:
        cat = r['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nSummary by category:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}")

if __name__ == '__main__':
    populate_catalog()
