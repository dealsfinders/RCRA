#!/bin/bash
# RCRA Quick Commands Reference

# ============================================
# DEPLOYMENT COMMANDS
# ============================================

# Build the application
cd /Users/selva/Documents/Project/RCRA/infra
sam build

# Deploy the application
sam deploy

# Deploy with different parameters
sam deploy --parameter-overrides BedrockRegion=us-east-1 LogGroupName=/your/custom/log-group

# ============================================
# TESTING COMMANDS
# ============================================

# Create a test error
LOG_STREAM="test-$(date +%s)"
aws logs create-log-stream \
  --log-group-name /aws/lambda/rcra-test-app \
  --log-stream-name $LOG_STREAM \
  --region us-east-1

aws logs put-log-events \
  --log-group-name /aws/lambda/rcra-test-app \
  --log-stream-name $LOG_STREAM \
  --log-events timestamp=$(date +%s000),message='ERROR: Test error message' \
  --region us-east-1

# ============================================
# MONITORING COMMANDS
# ============================================

# List recent Step Functions executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:879381275427:stateMachine:RCRAStateMachine \
  --max-items 10 \
  --region us-east-1

# Get specific execution details
aws stepfunctions describe-execution \
  --execution-arn <EXECUTION_ARN> \
  --region us-east-1

# Get execution history
aws stepfunctions get-execution-history \
  --execution-arn <EXECUTION_ARN> \
  --region us-east-1

# View Lambda function logs (follow mode)
aws logs tail /aws/lambda/rcra-analyzer --follow --region us-east-1
aws logs tail /aws/lambda/rcra-log-ingest --follow --region us-east-1
aws logs tail /aws/lambda/rcra-remediator --follow --region us-east-1
aws logs tail /aws/lambda/rcra-persist --follow --region us-east-1

# ============================================
# DYNAMODB QUERIES
# ============================================

# Scan all records
aws dynamodb scan \
  --table-name RCRARootCauseTable \
  --region us-east-1 \
  --max-items 10

# Get specific incident
aws dynamodb get-item \
  --table-name RCRARootCauseTable \
  --key '{"IncidentId": {"S": "inc-XXXXX"}}' \
  --region us-east-1

# Query recent records with filter
aws dynamodb scan \
  --table-name RCRARootCauseTable \
  --region us-east-1 \
  --filter-expression "attribute_exists(CreatedAt)"

# ============================================
# SNS COMMANDS
# ============================================

# List subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:879381275427:RCRANotifications \
  --region us-east-1

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:879381275427:RCRANotifications \
  --protocol email \
  --notification-endpoint your-email@example.com \
  --region us-east-1

# Subscribe SMS
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:879381275427:RCRANotifications \
  --protocol sms \
  --notification-endpoint +1234567890 \
  --region us-east-1

# Unsubscribe
aws sns unsubscribe \
  --subscription-arn <SUBSCRIPTION_ARN> \
  --region us-east-1

# ============================================
# CLOUDWATCH LOGS COMMANDS
# ============================================

# List log groups
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/rcra \
  --region us-east-1

# Create new log group
aws logs create-log-group \
  --log-group-name /your/custom/log-group \
  --region us-east-1

# List subscription filters
aws logs describe-subscription-filters \
  --log-group-name /aws/lambda/rcra-test-app \
  --region us-east-1

# ============================================
# CLEANUP COMMANDS
# ============================================

# Delete the entire stack
aws cloudformation delete-stack \
  --stack-name rcra-stack \
  --region us-east-1

# Delete S3 bucket (must be empty first)
aws s3 rm s3://rcra-sam-deployments-879381275427 --recursive
aws s3 rb s3://rcra-sam-deployments-879381275427

# Delete test log group
aws logs delete-log-group \
  --log-group-name /aws/lambda/rcra-test-app \
  --region us-east-1

# ============================================
# BEDROCK COMMANDS
# ============================================

# List available models
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude`)]'

# Check specific model
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query "modelSummaries[?modelId=='anthropic.claude-3-sonnet-20240229-v1:0']"

# ============================================
# USEFUL ALIASES (Add to ~/.zshrc or ~/.bashrc)
# ============================================

# alias rcra-logs='aws logs tail /aws/lambda/rcra-analyzer --follow'
# alias rcra-executions='aws stepfunctions list-executions --state-machine-arn arn:aws:states:us-east-1:879381275427:stateMachine:RCRAStateMachine --max-items 10'
# alias rcra-db='aws dynamodb scan --table-name RCRARootCauseTable --max-items 10'
# alias rcra-deploy='cd /Users/selva/Documents/Project/RCRA/infra && sam build && sam deploy'

echo "RCRA Commands loaded! Use the above commands to manage your RCRA system."



