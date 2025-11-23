# RCRA Email Notification Examples

## 📧 What You'll Receive

Every time RCRA detects an error and performs auto-remediation, you'll receive a detailed email at **selvaonline@gmail.com**.

---

## ✅ Example 1: Successful Auto-Remediation

**Subject**: `[RCRA] ✅ AUTO-FIXED: MEDIUM - inc-abc123`

**Email Body**:

```
╔══════════════════════════════════════════════════════════════════╗
║          RCRA - Root Cause & Remediation Alert                   ║
╚══════════════════════════════════════════════════════════════════╝

INCIDENT DETAILS
================
Incident ID: inc-abc123
Timestamp: 2025-11-23 16:00:00 UTC
Severity: MEDIUM
Log Group: /aws/lambda/my-production-app
Log Stream: 2025/11/23/[$LATEST]abc123

AI ANALYSIS
===========
Summary: Lambda function timed out due to insufficient timeout setting

Root Cause:
The configured timeout value of 30 seconds was too low for the workload
being processed by the Lambda function, causing it to time out before
completing execution.

AUTO-REMEDIATION STATUS
=======================
Eligible for Auto-Fix: YES
Action Taken: AUTO_REMEDIATED

✅ SUCCESSFULLY AUTO-REMEDIATED!

Details: Increased Lambda timeout from 30s to 60s

AWS Actions Performed:

  • Service: lambda
  • Action: update_function_configuration
  • Resource: my-production-app
  • Changes: {
        "timeout_before": 30,
        "timeout_after": 60
    }

✨ The issue has been automatically resolved. No manual intervention needed.

SUGGESTED REMEDIATION STEPS (from AI Analysis)
===============================================
1. Increase the Lambda function's timeout setting to a higher value
2. Optimize the Lambda function's code to reduce execution time
3. Consider breaking down the workload into smaller chunks
4. Monitor the Lambda function's execution time going forward

Tags: Lambda, Timeout, Performance, Configuration

RAW ERROR LOG
=============
ERROR: Lambda timeout - Operation took too long to complete.
Current timeout setting is insufficient for this workload...

══════════════════════════════════════════════════════════════════
View full details in the RCRA Dashboard:
http://localhost:8080/index.html
══════════════════════════════════════════════════════════════════
```

---

## ⚠️ Example 2: Auto-Remediation Failed

**Subject**: `[RCRA] ⚠️ AUTO-FIX FAILED: HIGH - inc-def456`

**Email Body**:

```
╔══════════════════════════════════════════════════════════════════╗
║          RCRA - Root Cause & Remediation Alert                   ║
╚══════════════════════════════════════════════════════════════════╝

INCIDENT DETAILS
================
Incident ID: inc-def456
Timestamp: 2025-11-23 16:05:00 UTC
Severity: HIGH
Log Group: /aws/lambda/my-api-service
Log Stream: 2025/11/23/[$LATEST]def456

AI ANALYSIS
===========
Summary: Database connection pool exhausted

Root Cause:
All connections in the database connection pool are busy or have timed out,
preventing new connections from being established.

AUTO-REMEDIATION STATUS
=======================
Eligible for Auto-Fix: YES
Action Taken: FAILED

⚠️ AUTO-REMEDIATION FAILED

Details: Failed to restart Lambda: Permission denied for UpdateFunctionConfiguration

Manual intervention is required. Please review the incident in the dashboard.

SUGGESTED REMEDIATION STEPS (from AI Analysis)
===============================================
1. Check IAM permissions for the remediator Lambda
2. Manually restart the Lambda function
3. Review connection pool configuration
4. Consider increasing max connections

══════════════════════════════════════════════════════════════════
```

---

## 👤 Example 3: Manual Approval Required

**Subject**: `[RCRA] 👤 APPROVAL NEEDED: CRITICAL - inc-ghi789`

**Email Body**:

```
╔══════════════════════════════════════════════════════════════════╗
║          RCRA - Root Cause & Remediation Alert                   ║
╚══════════════════════════════════════════════════════════════════╝

INCIDENT DETAILS
================
Incident ID: inc-ghi789
Timestamp: 2025-11-23 16:10:00 UTC
Severity: CRITICAL
Log Group: /aws/lambda/production-payment-processor
Log Stream: 2025/11/23/[$LATEST]ghi789

AI ANALYSIS
===========
Summary: Payment processing Lambda experiencing memory issues

Root Cause:
Lambda function is running out of allocated memory during peak processing

AUTO-REMEDIATION STATUS
=======================
Eligible for Auto-Fix: NO
Action Taken: MANUAL_APPROVAL_REQUIRED

👤 MANUAL APPROVAL REQUIRED

Details: Function production-payment-processor is marked as critical
and requires manual approval for memory changes.

This is a critical function that requires human approval before remediation.
Please review and approve the suggested actions in the dashboard.

SUGGESTED REMEDIATION STEPS (from AI Analysis)
===============================================
1. Review current memory usage patterns
2. Increase memory allocation from 1024MB to 2048MB
3. Test in staging environment first
4. Deploy to production after validation

══════════════════════════════════════════════════════════════════
```

---

## 📊 Example 4: Analysis Only (No Auto-Fix)

**Subject**: `[RCRA] 📊 NEW INCIDENT: LOW - inc-jkl012`

**Email Body**:

```
╔══════════════════════════════════════════════════════════════════╗
║          RCRA - Root Cause & Remediation Alert                   ║
╚══════════════════════════════════════════════════════════════════╝

INCIDENT DETAILS
================
Incident ID: inc-jkl012
Timestamp: 2025-11-23 16:15:00 UTC
Severity: LOW
Log Group: /aws/lambda/background-job-processor
Log Stream: 2025/11/23/[$LATEST]jkl012

AI ANALYSIS
===========
Summary: Intermittent API throttling detected

Root Cause:
API requests are occasionally exceeding rate limits during traffic spikes

AUTO-REMEDIATION STATUS
=======================
Eligible for Auto-Fix: YES
Action Taken: ANALYSIS_ONLY

📊 ANALYSIS COMPLETED

Details: API throttling detected. CloudWatch alarm created.
Recommend reviewing quota limits.

No automatic remediation was performed. Please review the suggested steps below.

SUGGESTED REMEDIATION STEPS (from AI Analysis)
===============================================
1. Review current API Gateway rate limits
2. Consider implementing request caching
3. Add exponential backoff to client code
4. Submit AWS Support ticket for quota increase if needed

Tags: API Gateway, Throttling, Rate Limiting

══════════════════════════════════════════════════════════════════
```

---

## 🎯 Email Notification Features

### Subject Line Indicators

- **✅ AUTO-FIXED** - Issue was automatically resolved
- **⚠️ AUTO-FIX FAILED** - Attempted fix failed, needs attention
- **👤 APPROVAL NEEDED** - Critical function, needs manual approval
- **📊 NEW INCIDENT** - Analysis completed, no auto-fix attempted

### Information Included

1. **Incident Details**

   - Unique incident ID
   - Timestamp
   - Severity level
   - Source log location

2. **AI Analysis**

   - Human-readable summary
   - Root cause explanation
   - Suggested remediation steps
   - Relevant tags

3. **Auto-Remediation Status**

   - Whether auto-fix was attempted
   - Action taken
   - AWS resources modified
   - Success/failure details

4. **Raw Error Log**

   - First 500 characters of the error
   - Helps with quick diagnosis

5. **Quick Links**
   - Direct link to dashboard
   - Link to documentation

---

## 📧 Confirming Your Subscription

**IMPORTANT**: You must confirm your email subscription before receiving notifications!

### Steps to Confirm:

1. **Check your email** at `selvaonline@gmail.com`
2. **Look for email from** `no-reply@sns.amazonaws.com`
3. **Subject will be**: "AWS Notification - Subscription Confirmation"
4. **Click the "Confirm subscription" link** in the email
5. **You'll see a confirmation page** in your browser

### If you don't see the confirmation email:

- Check your **Spam/Junk** folder
- The email might be filtered as bulk mail
- Try adding `no-reply@sns.amazonaws.com` to your contacts
- Resend the confirmation:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:879381275427:RCRANotifications \
  --protocol email \
  --notification-endpoint selvaonline@gmail.com \
  --region us-east-1
```

---

## 🧪 Testing Email Notifications

### Trigger Different Scenarios:

```bash
# 1. Timeout Error (will attempt auto-remediation)
LOG_STREAM="test-$(date +%s)"
aws logs create-log-stream --log-group-name /aws/lambda/rcra-test-app --log-stream-name $LOG_STREAM
aws logs put-log-events --log-group-name /aws/lambda/rcra-test-app --log-stream-name $LOG_STREAM \
  --log-events timestamp=$(date +%s000),message="ERROR: Lambda timeout - Increase timeout needed"

# 2. Memory Error (will attempt auto-remediation)
LOG_STREAM="test-$(date +%s)"
aws logs create-log-stream --log-group-name /aws/lambda/rcra-test-app --log-stream-name $LOG_STREAM
aws logs put-log-events --log-group-name /aws/lambda/rcra-test-app --log-stream-name $LOG_STREAM \
  --log-events timestamp=$(date +%s000),message="ERROR: OutOfMemoryError - Peak usage 510MB/512MB"

# 3. Connection Pool Error
LOG_STREAM="test-$(date +%s)"
aws logs create-log-stream --log-group-name /aws/lambda/rcra-test-app --log-stream-name $LOG_STREAM
aws logs put-log-events --log-group-name /aws/lambda/rcra-test-app --log-stream-name $LOG_STREAM \
  --log-events timestamp=$(date +%s000),message="ERROR: ConnectionPoolExhausted - All connections busy"
```

### Expected Email Timeline:

1. **Error written to CloudWatch**: Immediate
2. **RCRA detects error**: 10-15 seconds
3. **AI analysis completed**: 5-10 seconds
4. **Auto-remediation attempted**: 5-10 seconds
5. **Email sent**: Immediate after processing
6. **Email arrives in inbox**: 1-2 minutes

**Total time**: ~30 seconds to 2 minutes from error to email

---

## 🔔 Email Notification Settings

### Current Configuration:

- **Email**: selvaonline@gmail.com
- **Topic**: RCRANotifications
- **Region**: us-east-1
- **Status**: Pending Confirmation ⚠️

### To Add Additional Recipients:

```bash
# Add another team member
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:879381275427:RCRANotifications \
  --protocol email \
  --notification-endpoint teammate@company.com \
  --region us-east-1

# Add SMS notifications
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:879381275427:RCRANotifications \
  --protocol sms \
  --notification-endpoint +1234567890 \
  --region us-east-1
```

### To Unsubscribe:

```bash
# List subscriptions to get ARN
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:879381275427:RCRANotifications

# Unsubscribe using the ARN
aws sns unsubscribe --subscription-arn <SUBSCRIPTION_ARN>
```

---

## 💡 Pro Tips

1. **Set up email filters** to automatically label RCRA emails
2. **Create rules** to prioritize AUTO-FIX FAILED emails
3. **Forward critical alerts** to your on-call rotation
4. **Archive successful auto-fixes** for audit trail
5. **Review weekly summaries** to identify patterns

---

## 🎯 What To Do When You Receive an Email

### ✅ AUTO-FIXED

- **Action**: None required
- **Optional**: Review to understand what was fixed
- **Archive** for your records

### ⚠️ AUTO-FIX FAILED

- **Action**: Immediate - review and fix manually
- **Check**: Dashboard for full details
- **Investigate**: Why auto-fix failed
- **Update**: Remediation logic if needed

### 👤 APPROVAL NEEDED

- **Action**: Review the suggested remediation
- **Approve**: If changes are safe
- **Manually apply**: The recommended fix
- **Monitor**: Post-fix behavior

### 📊 NEW INCIDENT

- **Action**: Review suggested steps
- **Decide**: If manual intervention needed
- **Monitor**: If it recurs
- **Update**: Patterns if it's a new issue type

---

Remember: Email notifications keep you informed without overwhelming you. Auto-remediation handles the routine, you handle the exceptional! 📧✨


