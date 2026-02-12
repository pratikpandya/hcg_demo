# Load Testing - HCG Demo

**Status**: Ready for Execution  
**Target**: 500 concurrent users  
**Tool**: Locust

## Quick Start

### 1. Configure AWS Resources
```bash
python configure_load_test.py
```

**What it does**:
- Sets Lambda reserved concurrency (100 per function)
- Configures DynamoDB auto-scaling (5-100 capacity)
- Prepares system for high load

### 2. Run Load Test
```bash
python run_load_test.py
```

**Test Configuration**:
- Users: 500 concurrent
- Spawn Rate: 10 users/second
- Duration: 5 minutes
- Generates HTML report

### 3. View Results
Open `load_test_report.html` in browser

---

## Test Scenarios

### Query Distribution
- **KB Queries** (40%): HR, IT, Finance, General queries
- **Ticket Creation** (20%): ServiceNow incident creation
- **Feedback** (10%): User feedback submission
- **Other** (30%): Mixed interactions

### Sample Queries
**HR**: "What are the HR benefits?", "How do I request leave?"  
**IT**: "My laptop is broken", "VPN not working"  
**Finance**: "How do I submit expenses?", "Expense policy"  
**General**: "Where is the office?", "Office hours"

---

## Expected Results

### Performance Targets
- ✅ P95 latency: <15 seconds
- ✅ Error rate: <1%
- ✅ No Lambda throttling
- ✅ DynamoDB auto-scales

### Resource Limits
- **Lambda**: 300 concurrent executions (100 per function)
- **DynamoDB**: Auto-scales 5-100 capacity units
- **API Gateway**: 10,000 requests/second (default)

---

## AWS Resource Configuration

### Lambda Functions
1. **hcg-demo-webhook-handler**
   - Reserved: 100 concurrent executions
   - Timeout: 60s
   - Memory: 512MB

2. **hcg-demo-supervisor-agent**
   - Reserved: 100 concurrent executions
   - Timeout: 60s
   - Memory: 512MB

3. **hcg-demo-servicenow-action**
   - Reserved: 100 concurrent executions
   - Timeout: 30s
   - Memory: 256MB

### DynamoDB Tables
1. **hcg-demo-conversations**
   - Auto-scaling: 5-100 read/write capacity
   - Target utilization: 70%

2. **hcg-demo-user-feedback**
   - Auto-scaling: 5-100 read/write capacity
   - Target utilization: 70%

---

## Monitoring During Test

### CloudWatch Metrics to Watch
1. **Lambda**:
   - Invocations
   - Duration (P95, P99)
   - Errors
   - Throttles
   - Concurrent Executions

2. **DynamoDB**:
   - ConsumedReadCapacityUnits
   - ConsumedWriteCapacityUnits
   - ThrottledRequests
   - UserErrors

3. **API Gateway**:
   - Count (requests)
   - Latency (P95, P99)
   - 4XXError
   - 5XXError

### CloudWatch Dashboard
View real-time metrics:
```
AWS Console → CloudWatch → Dashboards → HCG-Demo-Metrics
```

---

## Locust Web UI (Optional)

For interactive testing with web UI:

```bash
locust -f locust_test.py --host https://[api-id].execute-api.ap-southeast-1.amazonaws.com/prod
```

Then open: http://localhost:8089

---

## Test Results Interpretation

### Success Criteria
| Metric | Target | Status |
|--------|--------|--------|
| P95 Latency | <15s | Check report |
| Error Rate | <1% | Check report |
| Lambda Throttles | 0 | Check CloudWatch |
| DynamoDB Throttles | 0 | Check CloudWatch |

### Common Issues

**High Latency**:
- Check Lambda cold starts
- Verify KB query performance
- Check DynamoDB capacity

**Throttling**:
- Increase Lambda reserved concurrency
- Increase DynamoDB capacity limits
- Check API Gateway limits

**Errors**:
- Check Lambda logs in CloudWatch
- Verify DynamoDB table status
- Check API Gateway configuration

---

## Cost Estimation

### 5-Minute Load Test (500 users)
- **Lambda**: ~$2-5 (based on invocations)
- **DynamoDB**: ~$1-2 (based on capacity)
- **API Gateway**: ~$0.50 (based on requests)
- **CloudWatch**: Included in free tier
- **Total**: ~$3.50-7.50 per test

### Optimization Tips
1. Use provisioned concurrency for Lambda (if frequent testing)
2. Use DynamoDB on-demand pricing (if infrequent testing)
3. Run tests during off-peak hours
4. Clean up test data after completion

---

## Files Created

1. **locust_test.py** - Locust test script
2. **run_load_test.py** - Test runner
3. **configure_load_test.py** - AWS resource configuration
4. **LOAD_TEST_GUIDE.md** - This documentation

---

## Troubleshooting

### Locust Not Installed
```bash
pip install locust
```

### API Gateway URL Not Found
Manually set in `run_load_test.py`:
```python
host = "https://[your-api-id].execute-api.ap-southeast-1.amazonaws.com/prod"
```

### Lambda Throttling
Increase reserved concurrency:
```bash
aws lambda put-function-concurrency \
  --function-name hcg-demo-webhook-handler \
  --reserved-concurrent-executions 200
```

### DynamoDB Throttling
Increase capacity limits in `configure_load_test.py`:
```python
MaxCapacity=200  # Instead of 100
```

---

## Post-Test Cleanup

### Reset Lambda Concurrency
```bash
aws lambda delete-function-concurrency --function-name hcg-demo-webhook-handler
```

### Remove DynamoDB Auto-Scaling
```bash
aws application-autoscaling deregister-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/hcg-demo-conversations \
  --scalable-dimension dynamodb:table:ReadCapacityUnits
```

### Clear Test Data
```python
# Script to clear test conversations
import boto3
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
table = dynamodb.Table('hcg-demo-conversations')
# Scan and delete test records
```

---

## Next Steps

1. **Baseline Test**: Run with 50 users to establish baseline
2. **Ramp Up**: Gradually increase to 500 users
3. **Analyze**: Review metrics and identify bottlenecks
4. **Optimize**: Adjust resources based on results
5. **Repeat**: Re-test after optimizations

---

**Status**: ⏳ Ready for execution (deferred to post-pilot)  
**Priority**: 🟢 Nice-to-have  
**Estimated Duration**: 10-15 minutes (including setup)
