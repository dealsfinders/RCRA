# RCRA – Root Cause & Remediation Assistant (MVP)

Serverless MVP that ingests CloudWatch errors, runs RCA via Bedrock, optionally simulates remediation, stores results, and notifies engineers.

## Repo layout
- infra/template.yaml – AWS SAM template (DynamoDB, SNS, Lambda functions, Step Functions)
- src/log_ingest_lambda.py – CloudWatch Logs subscription; starts state machine
- src/rca_analyzer_lambda.py – Calls Bedrock for structured RCA JSON
- src/remediator_lambda.py – Simple auto-remediation eligibility + simulated action
- src/persist_lambda.py – Writes RCA to DynamoDB and publishes to SNS

## Prerequisites
- AWS CLI/SAM CLI configured
- Bedrock access in target region (default us-east-1; override via parameter)
- SNS subscription configured after deploy (email/SMS)

## Deploy
```bash
cd infra
sam build
sam deploy --guided \
  --stack-name rcra-mvp-stack \
  --parameter-overrides LogGroupName=/aws/lambda/your-app-log-group BedrockRegion=us-east-1
```

Provide email for SNS subscription when prompted in the console, then confirm the subscription.

## How it works
1) CloudWatch Logs with `"ERROR"` hit log_ingest → Step Functions execution starts.  
2) analyzer → Bedrock → structured RCA JSON.  
3) remediator → flags HIGH/CRITICAL for simulated restart.  
4) persist → DynamoDB record + SNS notification.
