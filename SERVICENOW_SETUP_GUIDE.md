# ServiceNow Integration Configuration Guide

## Quick Setup (3 Steps)

### Step 1: Configure ServiceNow Credentials
```bash
python configure_servicenow.py
```

**You'll be prompted for**:
- ServiceNow Instance URL (e.g., `https://dev12345.service-now.com`)
- Username (e.g., `admin`)
- Password
- OAuth Client ID (optional)
- OAuth Client Secret (optional)

**What it does**:
- Securely stores credentials in AWS Systems Manager Parameter Store (encrypted)
- Creates `servicenow_config.json` with configuration summary

---

### Step 2: Update Lambda Function
```bash
python update_servicenow_lambda.py
```

**What it does**:
- Adds SSM read permissions to Lambda IAM role
- Updates `hcg-demo-servicenow-action` Lambda with new code
- Configures 30-second timeout

---

### Step 3: Test Integration
```bash
python test_servicenow_integration.py
```

**What it tests**:
- Creates a test incident in ServiceNow
- Retrieves incident status
- Validates full integration

**Expected output**:
```
✅ Incident created successfully!

Incident Details:
  Number: INC0012345
  Sys ID: abc123...
  Priority: 2
  Link: https://your-instance.service-now.com/nav_to.do?uri=incident.do?sys_id=abc123
```

---

## What You Need

### ServiceNow Instance Information

1. **Instance URL**
   - Format: `https://[instance-name].service-now.com`
   - Example: `https://dev12345.service-now.com`
   - Find it: ServiceNow login page URL

2. **Username**
   - ServiceNow user with incident creation permissions
   - Recommended: Service account (not personal account)
   - Required roles: `itil`, `incident_manager`

3. **Password**
   - Password for the ServiceNow user
   - Will be encrypted in AWS Parameter Store

4. **OAuth Credentials** (Optional but recommended for production)
   - Client ID
   - Client Secret
   - Setup: ServiceNow → System OAuth → Application Registry

---

## Security

### Credentials Storage
- ✅ Stored in AWS Systems Manager Parameter Store
- ✅ Password encrypted with AWS KMS
- ✅ Never stored in code or logs
- ✅ Cached in Lambda for 5 minutes only

### IAM Permissions
Lambda needs:
- `ssm:GetParameters` - Read credentials
- `kms:Decrypt` - Decrypt password

---

## Troubleshooting

### Error: "ServiceNow credentials not configured"
**Solution**: Run `python configure_servicenow.py` first

### Error: "HTTP 401: Unauthorized"
**Causes**:
- Wrong username/password
- User lacks permissions

**Solution**: 
1. Verify credentials in ServiceNow
2. Check user has `itil` role
3. Re-run `python configure_servicenow.py`

### Error: "HTTP 403: Forbidden"
**Cause**: User lacks incident creation permissions

**Solution**: Add `incident_manager` role to ServiceNow user

### Error: "Connection timeout"
**Causes**:
- Wrong instance URL
- Network/firewall issue

**Solution**:
1. Verify instance URL is correct
2. Check Lambda has internet access (NAT Gateway if in VPC)

---

## Files Created

1. **configure_servicenow.py** - Credential configuration script
2. **lambda_servicenow_action_updated.py** - Updated Lambda code
3. **update_servicenow_lambda.py** - Lambda deployment script
4. **test_servicenow_integration.py** - Integration test script
5. **servicenow_config.json** - Configuration summary (created after Step 1)

---

## AWS Resources Modified

### Systems Manager Parameters (Created)
- `/hcg-demo/servicenow/instance-url` - Instance URL
- `/hcg-demo/servicenow/username` - Username
- `/hcg-demo/servicenow/password` - Password (encrypted)
- `/hcg-demo/servicenow/client-id` - OAuth client ID (if provided)
- `/hcg-demo/servicenow/client-secret` - OAuth secret (if provided, encrypted)

### Lambda Function (Updated)
- **Name**: `hcg-demo-servicenow-action`
- **Changes**: 
  - Reads credentials from Parameter Store
  - Implements credential caching
  - Timeout increased to 30s

### IAM Role (Updated)
- **Role**: `hcg-demo-lambda-role`
- **Added Policy**: `AmazonSSMReadOnlyAccess`

---

## API Endpoints

### Create Incident
```json
{
  "actionGroup": "ServiceNowActions",
  "apiPath": "/create_incident",
  "httpMethod": "POST",
  "parameters": [
    {"name": "short_description", "value": "Issue summary"},
    {"name": "description", "value": "Detailed description"},
    {"name": "category", "value": "Network"},
    {"name": "urgency", "value": "2"}
  ]
}
```

### Get Incident Status
```json
{
  "actionGroup": "ServiceNowActions",
  "apiPath": "/get_incident_status",
  "httpMethod": "GET",
  "parameters": [
    {"name": "incident_number", "value": "INC0012345"}
  ]
}
```

---

## Production Checklist

- [ ] Use service account (not personal account)
- [ ] Configure OAuth (recommended over basic auth)
- [ ] Test incident creation
- [ ] Test incident status retrieval
- [ ] Verify user permissions in ServiceNow
- [ ] Set up monitoring/alerts
- [ ] Document incident categories used
- [ ] Configure SLA rules in ServiceNow

---

## Support

**ServiceNow Documentation**: https://docs.servicenow.com/  
**AWS Parameter Store**: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

---

**Quick Start**: Run these 3 commands in order:
```bash
python configure_servicenow.py
python update_servicenow_lambda.py
python test_servicenow_integration.py
```
