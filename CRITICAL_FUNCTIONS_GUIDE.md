# Critical Functions Configuration Guide

## Overview

The RCRA system now supports marking functions as "critical" to require manual approval before any auto-remediation actions are performed. This is essential for:

- Production payment processing systems
- Authentication and authorization services
- Financial transaction handlers
- Customer data processors
- Any mission-critical service where manual review is required

## How It Works

### Normal Flow (Non-Critical Functions)

```
Error Detected → AI Analysis → Auto-Remediation → ✅ AUTO-FIXED → Email Notification
```

### Critical Function Flow

```
Error Detected → AI Analysis → 🛑 APPROVAL REQUIRED → Manual Review → Manual Fix → Email Notification
```

## Configuration API

### Base URL

```
https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions
```

### View Current Critical Functions

```bash
curl https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions
```

**Response:**

```json
{
  "success": true,
  "criticalFunctions": ["prod-payment-processor", "prod-auth-service"],
  "count": 2
}
```

### Add a Critical Function

```bash
curl -X POST https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions \
  -H "Content-Type: application/json" \
  -d '{
    "action": "add",
    "functionName": "production-payment-processor"
  }'
```

**Response:**

```json
{
  "success": true,
  "criticalFunctions": [
    "prod-payment-processor",
    "prod-auth-service",
    "production-payment-processor"
  ],
  "message": "Critical functions updated. Total: 3"
}
```

### Remove a Critical Function

```bash
curl -X POST https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions \
  -H "Content-Type: application/json" \
  -d '{
    "action": "remove",
    "functionName": "production-payment-processor"
  }'
```

**Response:**

```json
{
  "success": true,
  "criticalFunctions": ["prod-payment-processor", "prod-auth-service"],
  "message": "Critical functions updated. Total: 2"
}
```

### Bulk Update (Replace All)

```bash
curl -X POST https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions \
  -H "Content-Type: application/json" \
  -d '{
    "functions": [
      "prod-payment-processor",
      "prod-auth-service",
      "prod-financial-transactions",
      "prod-customer-data-handler"
    ]
  }'
```

## Function Name Format

The function name should match the Lambda function name as it appears in the log group.

**Log Group Format:** `/aws/lambda/FUNCTION-NAME`
**Function Name:** `FUNCTION-NAME`

### Examples:

| Log Group                             | Function Name to Use      |
| ------------------------------------- | ------------------------- |
| `/aws/lambda/prod-payment-api`        | `prod-payment-api`        |
| `/aws/lambda/production-auth-service` | `production-auth-service` |
| `/aws/lambda/app-prod-payments`       | `app-prod-payments`       |

## Remediation Status Meanings

### ✅ AUTO-FIXED (AUTO_REMEDIATED)

- **What:** System automatically resolved the issue
- **Action:** None required, review the changes made
- **Example:** Lambda timeout increased from 30s to 60s

### ⚠️ FAILED

- **What:** System attempted auto-fix but encountered an error
- **Action:** Immediate manual intervention required
- **Example:** Insufficient permissions to update function configuration

### 👤 APPROVAL NEEDED (MANUAL_APPROVAL_REQUIRED)

- **What:** Function is marked as critical, auto-fix blocked
- **Action:** Review AI analysis and suggested steps, then apply manually
- **Example:** Critical payment processor timeout - needs senior approval

### 📊 ANALYSIS ONLY

- **What:** No auto-remediation pattern matched, analysis only
- **Action:** Review AI suggestions and decide on manual remediation
- **Example:** Complex application logic error requiring code fix

## Email Notifications

### Auto-Fixed Email

```
Subject: [RCRA] ✅ AUTO-FIXED: MEDIUM - inc-abc123

Support Ticket: RCRA-2025-835516
Incident ID: inc-abc123

AUTO-REMEDIATION STATUS
=======================
✅ SUCCESSFULLY AUTO-REMEDIATED!
Details: Lambda timeout increased
AWS Actions Performed:
  • Service: Lambda
  • Action: UpdateFunctionConfiguration
  • Resource: rcra-test-app
  • Changes: {"Timeout": {"before": 3, "after": 60}}

✨ The issue has been automatically resolved!
```

### Approval Required Email

```
Subject: [RCRA] 👤 APPROVAL NEEDED: CRITICAL - inc-ghi789

Support Ticket: RCRA-2025-835516
Incident ID: inc-ghi789

AUTO-REMEDIATION STATUS
=======================
👤 APPROVAL REQUIRED!
Details: This function is marked as CRITICAL and requires manual approval

➡️ Review and approve manual remediation via dashboard or console.
```

## Support Team Workflow

### Step 1: Identify Critical Functions

Work with your team to identify which functions should require approval:

1. **Financial Systems:**

   - Payment processors
   - Transaction handlers
   - Billing systems

2. **Security Systems:**

   - Authentication services
   - Authorization handlers
   - Key management services

3. **Data Systems:**

   - Customer data processors
   - PII handlers
   - Compliance-related services

4. **Production Critical:**
   - High-traffic APIs
   - Core business logic
   - Revenue-generating services

### Step 2: Add Functions to Critical List

```bash
# Add production payment processor
curl -X POST https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions \
  -H "Content-Type: application/json" \
  -d '{"action": "add", "functionName": "prod-payment-processor"}'

# Add authentication service
curl -X POST https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions \
  -H "Content-Type: application/json" \
  -d '{"action": "add", "functionName": "prod-auth-service"}'

# Add financial transactions handler
curl -X POST https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions \
  -H "Content-Type: application/json" \
  -d '{"action": "add", "functionName": "prod-financial-transactions"}'
```

### Step 3: Verify Configuration

```bash
curl https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions
```

### Step 4: Monitor Incidents

1. **Watch for email notifications** with 👤 APPROVAL NEEDED status
2. **Review incidents in dashboard** with remediation badges
3. **Click incident** for full AI analysis and suggested steps
4. **Apply remediation manually** after approval from senior team

### Step 5: Periodic Review

Quarterly, review your critical functions list:

```bash
# Get current list
curl https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions

# Remove functions that can now be auto-fixed
curl -X POST https://76ckmapns1.execute-api.us-east-1.amazonaws.com/config/critical-functions \
  -H "Content-Type: application/json" \
  -d '{"action": "remove", "functionName": "old-test-function"}'
```

## Dashboard Integration

The dashboard now displays remediation status badges for all incidents:

### Recent Incidents View

```
╔═══════════════════════════════════════════════════════════════╗
║ 🎫 RCRA-2025-835516                              [MEDIUM]     ║
║ Lambda function timeout                                       ║
║ 11/23/2025, 10:34:37 AM                                      ║
║ 👤 APPROVAL - This is a critical function                    ║
╚═══════════════════════════════════════════════════════════════╝
```

### Incident Details Modal

- Full AI analysis
- Remediation status with icon
- AWS actions performed (for auto-fixed)
- Suggested manual steps (for approval required)
- Support ticket number
- Severity and tags

## Best Practices

### DO ✅

1. **Mark production payment systems as critical**
2. **Review critical list quarterly**
3. **Add new critical functions when deployed**
4. **Test auto-remediation on non-critical functions first**
5. **Document why each function is critical**
6. **Train team on approval workflow**

### DON'T ❌

1. **Mark all functions as critical** (defeats the purpose)
2. **Mark test/dev functions as critical**
3. **Forget to remove decommissioned functions**
4. **Skip reviewing AI suggestions** (they're valuable even if approval needed)
5. **Auto-approve without understanding the issue**

## Troubleshooting

### Q: How do I find my function names?

```bash
# List all Lambda functions
aws lambda list-functions --query 'Functions[*].FunctionName'

# Check CloudWatch Log Groups
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/" \
  --query 'logGroups[*].logGroupName'
```

### Q: What happens if I add a non-existent function?

The system will store it, and if that function starts logging errors in the future, it will be treated as critical.

### Q: Can I use wildcards?

No, exact function names only. Use your CI/CD to update the list when deploying new services.

### Q: What if the API is down?

The system defaults to **safe mode** - if it cannot check the critical functions list, it will **NOT** perform auto-remediation.

### Q: How do I integrate this with my deployment pipeline?

```bash
# Add to your deployment script
FUNCTION_NAME="my-new-critical-service"

# After deploying to production, mark as critical
if [ "$ENVIRONMENT" == "production" ]; then
  curl -X POST $API_ENDPOINT/config/critical-functions \
    -H "Content-Type: application/json" \
    -d "{\"action\": \"add\", \"functionName\": \"$FUNCTION_NAME\"}"
fi
```

## Security Considerations

### Access Control

The `/config/critical-functions` endpoint should be restricted to:

- Senior SRE team members
- DevOps leads
- System administrators

Consider adding:

1. API Gateway API keys
2. AWS IAM authentication
3. Rate limiting
4. Audit logging

### Configuration File (future enhancement)

For better version control, consider storing your critical functions in a configuration file:

```yaml
# critical-functions.yaml
critical_functions:
  - prod-payment-processor
  - prod-auth-service
  - prod-financial-transactions
  - prod-customer-data-handler

approval_required_severities:
  - CRITICAL
  - HIGH

notification_email: ops-team@example.com
```

## Example Scenarios

### Scenario 1: Payment Processor Timeout

**Before Critical Configuration:**

```
Error → AI Analysis → ⚡ Auto-increase timeout → ✅ AUTO-FIXED
```

**After Critical Configuration:**

```
Error → AI Analysis → 🛑 Critical check → 👤 APPROVAL REQUIRED → Email sent →
Senior engineer reviews → Manual timeout increase → Document change → Done
```

### Scenario 2: Test Function Memory Error

**Not Critical:**

```
Error → AI Analysis → ⚡ Auto-increase memory → ✅ AUTO-FIXED
(Save support team time!)
```

### Scenario 3: Auth Service Connection Pool

**Critical Function:**

```
Error → AI Analysis → 🛑 Critical check → 👤 APPROVAL REQUIRED →
Security team reviews → Check for security implications →
Increase connection pool → Done
```

## API Reference Summary

| Method | Endpoint                     | Purpose                     | Request Body                                  |
| ------ | ---------------------------- | --------------------------- | --------------------------------------------- |
| GET    | `/config/critical-functions` | List all critical functions | None                                          |
| POST   | `/config/critical-functions` | Add one function            | `{"action": "add", "functionName": "..."}`    |
| POST   | `/config/critical-functions` | Remove one function         | `{"action": "remove", "functionName": "..."}` |
| POST   | `/config/critical-functions` | Replace all functions       | `{"functions": ["...", "..."]}`               |

## Support

For questions or issues:

1. Check dashboard for incident details
2. Review CloudWatch Logs for RCRA State Machine
3. Check DynamoDB table `RCRARootCauseTable`
4. Review email notifications
5. Contact DevOps team

## Version History

- **v2.0** (2025-11-23): Added critical functions configuration
- **v1.5** (2025-11-23): Added support ticket numbers
- **v1.0** (2025-11-22): Initial RCRA system with auto-remediation

---

**Remember:** The goal is to save support team time while maintaining control over critical systems. Balance automation with safety!









