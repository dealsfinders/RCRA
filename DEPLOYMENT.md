# RCRA Deployment Summary

## ✅ Deployment Completed Successfully

**Date**: November 22, 2025  
**AWS Account**: 879381275427  
**Region**: us-east-1  
**User**: selvaonline

---

## Deployed Resources

### DynamoDB

- **Table Name**: `RCRARootCauseTable`
- **Purpose**: Stores root cause analysis records

### Step Functions

- **State Machine ARN**: `arn:aws:states:us-east-1:879381275427:stateMachine:RCRAStateMachine`
- **Purpose**: Orchestrates the RCA workflow (Analyze → Remediate → Persist)

### Lambda Functions

1. **rcra-log-ingest**: Monitors CloudWatch logs and triggers Step Functions
2. **rcra-analyzer**: Uses Claude AI (Bedrock) for root cause analysis
3. **rcra-remediator**: Determines auto-remediation eligibility
4. **rcra-persist**: Saves to DynamoDB and sends SNS notifications

### SNS Topic

- **Topic ARN**: `arn:aws:sns:us-east-1:879381275427:RCRANotifications`
- **Subscriptions**: selvaonline@gmail.com (pending confirmation)

### CloudWatch Log Group

- **Log Group**: `/aws/lambda/rcra-test-app`
- **Purpose**: Test log group for triggering errors

---

## Configuration Details

### Bedrock Model

- **Model ID**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **Region**: us-east-1
- **Status**: Available and working

### SAM Configuration

- **Stack Name**: rcra-stack
- **S3 Bucket**: rcra-sam-deployments-879381275427
- **Runtime**: Python 3.12

---

## Test Results

### Test Execution

- **Status**: ✅ SUCCEEDED
- **Execution ARN**: `arn:aws:states:us-east-1:879381275427:execution:RCRAStateMachine:e532a05b-24a8-462c-a7e2-5293d056e417`
- **Duration**: ~7 seconds

### Test Error Log

```
ERROR: NullPointerException in UserService.processPayment() - Payment processor returned null response.
This typically indicates a timeout or network connectivity issue with the payment gateway API.
```

### AI Analysis Results

- **Summary**: Payment processing failure due to timeout/network connectivity issue
- **Root Cause**: Payment gateway API timeout causing null response
- **Severity**: HIGH
- **Remediation Steps**:
  1. Check payment gateway API status and connectivity
  2. Implement retry logic with exponential backoff
  3. Add circuit breaker functionality
  4. Implement fallback logic for graceful failure handling
  5. Monitor gateway uptime and consider backup provider
- **Tags**: NullPointerException, payment, gateway, network, timeout, connectivity

---

## Next Steps

### 1. Confirm SNS Subscription

- Check email: `selvaonline@gmail.com`
- Click "Confirm subscription" link in the AWS SNS email
- Until confirmed, you won't receive notifications

### 2. Update Log Group (When Ready)

To monitor your production logs, update the CloudWatch log group:

```bash
cd /Users/selva/Documents/Project/RCRA/infra
# Edit samconfig.toml and change LogGroupName parameter
sam build
sam deploy
```

### 3. View Resources in AWS Console

- **Step Functions**: https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines
- **DynamoDB Table**: https://console.aws.amazon.com/dynamodbv2/home?region=us-east-1#tables
- **Lambda Functions**: https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups

### 4. Monitor System

```bash
# List recent executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:879381275427:stateMachine:RCRAStateMachine \
  --max-items 10

# Query DynamoDB records
aws dynamodb scan --table-name RCRARootCauseTable --max-items 10

# View Lambda logs
aws logs tail /aws/lambda/rcra-analyzer --follow
```

### 5. Trigger Test Errors

```bash
# Create a test error
LOG_STREAM="test-$(date +%s)"
aws logs create-log-stream \
  --log-group-name /aws/lambda/rcra-test-app \
  --log-stream-name $LOG_STREAM

aws logs put-log-events \
  --log-group-name /aws/lambda/rcra-test-app \
  --log-stream-name $LOG_STREAM \
  --log-events timestamp=$(date +%s000),message='ERROR: Your test error message here'
```

---

## Troubleshooting

### Check Lambda Function Logs

```bash
aws logs tail /aws/lambda/rcra-analyzer --follow
aws logs tail /aws/lambda/rcra-log-ingest --follow
```

### View Execution Details

```bash
aws stepfunctions describe-execution \
  --execution-arn <execution-arn-from-list>
```

### Common Issues

1. **SNS not sending emails**: Confirm subscription first
2. **Bedrock errors**: Ensure model access is enabled in Bedrock console
3. **No executions triggered**: Check CloudWatch subscription filter is active

---

## Cost Considerations

### Current Configuration

- **DynamoDB**: PAY_PER_REQUEST (only pay for what you use)
- **Lambda**: 512MB memory, likely stays in free tier for low volume
- **Step Functions**: $0.025 per 1,000 state transitions
- **Bedrock**: Pay per token (Claude 3 Sonnet pricing applies)
- **CloudWatch Logs**: Free tier covers most small workloads

### Estimated Monthly Cost (Low Volume)

- 100 errors/month: ~$2-5
- 1,000 errors/month: ~$15-25
- Most cost from Bedrock API calls

---

## Files Modified

1. `/Users/selva/Documents/Project/RCRA/infra/template.yaml`
   - Updated Python runtime to 3.12
2. `/Users/selva/Documents/Project/RCRA/src/rca_analyzer_lambda.py`
   - Fixed Bedrock API call to include anthropic_version
   - Fixed response parsing for Claude 3 API format
3. `/Users/selva/Documents/Project/RCRA/src/requirements.txt`
   - Created with boto3 dependency
4. `/Users/selva/Documents/Project/RCRA/infra/samconfig.toml`
   - Created with deployment configuration
   - S3 bucket: rcra-sam-deployments-879381275427
   - Log group: /aws/lambda/rcra-test-app

---

## System Architecture

```
CloudWatch Logs (/aws/lambda/rcra-test-app)
    ↓ (Subscription Filter: "ERROR")
rcra-log-ingest Lambda
    ↓ (StartExecution)
Step Functions State Machine
    ↓
    ├→ rcra-analyzer Lambda (Bedrock AI Analysis)
    ↓
    ├→ rcra-remediator Lambda (Determine Auto-Remediation)
    ↓
    └→ rcra-persist Lambda
        ├→ DynamoDB (RCRARootCauseTable)
        └→ SNS (Email/SMS Notifications)
```

---

## Support

For issues or questions:

1. Check CloudWatch Logs for Lambda errors
2. Review Step Functions execution history
3. Verify Bedrock model access in AWS Console
4. Ensure IAM permissions are correct (already set by SAM)









