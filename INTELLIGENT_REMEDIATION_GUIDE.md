# Intelligent Auto-Remediation System

**RCRA v4.0 - Intelligent Eligibility Engine**

Date: November 23, 2025  
Status: ✅ Deployed

---

## 🧠 Major Enhancements

### 1. Claude 3.5 Sonnet Integration

**Upgraded Model:**
- **Previous:** `anthropic.claude-3-sonnet-20240229-v1:0`
- **New:** `anthropic.claude-3-5-sonnet-20240620-v1:0`

**Benefits:**
- More accurate root cause analysis
- Better understanding of error patterns
- Improved remediation suggestions
- Enhanced reasoning about recurrence

### 2. Enhanced AI Analysis Fields

**New AI Output Fields:**

```json
{
  "summary": "Lambda timeout error",
  "probable_root_cause": "Insufficient timeout configuration",
  "severity": "MEDIUM",
  "suggested_remediation_steps": [...],
  "tags": [...],
  
  // NEW FIELDS:
  "recurrence_hint": "This error pattern has been seen before",
  "auto_remediation_candidate": true,
  "rationale": "High confidence timeout fix with low risk"
}
```

**Field Descriptions:**

| Field | Type | Purpose |
|-------|------|---------|
| `recurrence_hint` | string | AI's assessment of error familiarity |
| `auto_remediation_candidate` | boolean | AI's recommendation for auto-fix |
| `rationale` | string | AI's reasoning for the recommendation |

### 3. Intelligent Eligibility Gate

**Decision Logic:**

The system now uses **multi-factor eligibility** instead of simple pattern matching:

```
Auto-Remediation Proceeds If:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. NOT a critical function (still checked)
   AND
2. At least ONE of:
   a) Recurring issue (3+ times in 24h)
   b) High/Critical severity
   c) AI flagged as candidate
   d) Known scenario pattern
```

**Otherwise:** Returns `MANUAL_REVIEW_REQUIRED`

### 4. 24-Hour Recurrence Tracking

**How It Works:**

1. Extract error signature from AI summary
2. Query DynamoDB for similar errors in last 24h
3. Count occurrences
4. Flag if ≥ 3 occurrences (recurring)

**Benefits:**
- Identifies chronic issues
- Prioritizes frequent problems
- Reduces manual review for known issues

### 5. Scenario Detection

**Detected Scenarios:**

- `TIMEOUT` - Lambda timeout errors
- `MEMORY` - Memory/OOM errors
- `CONNECTION_POOL` - Connection exhaustion
- `THROTTLING` - Rate limit errors
- `CACHE_CORRUPTION` - Cache issues
- `HEALTH_CHECK` - Health check failures
- `DLQ` - Dead letter queue issues
- `UNKNOWN` - Unrecognized pattern

**Impact:**
- Better remediation matching
- Scenario-specific actions
- Improved success rate

---

## 🎯 Eligibility Decision Flow

```
┌─────────────────────────────────────┐
│   Error Detected in CloudWatch      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   AI Analysis (Claude 3.5 Sonnet)   │
│   • Summary, Root Cause, Severity   │
│   • Recurrence Hint                 │
│   • Auto-remediation Candidate      │
│   • Rationale                       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Enhanced Remediator               │
│   Step 1: Critical Function Check   │
└──────────────┬──────────────────────┘
               ↓
         [Is Critical?]
               ├─ YES → MANUAL_APPROVAL_REQUIRED
               └─ NO → Continue
                       ↓
         ┌─────────────────────────────┐
         │ Step 2: Scenario Detection  │
         │ • Pattern matching          │
         │ • Error signature           │
         └──────────┬──────────────────┘
                    ↓
         ┌─────────────────────────────┐
         │ Step 3: Recurrence Check    │
         │ • Query DynamoDB            │
         │ • Count occurrences (24h)   │
         │ • Flag if ≥ 3 times         │
         └──────────┬──────────────────┘
                    ↓
         ┌─────────────────────────────┐
         │ Step 4: Eligibility Gate    │
         │                             │
         │ Eligible if ANY of:         │
         │ • Recurring (≥3 times)      │
         │ • High/Critical severity    │
         │ • AI recommends (candidate) │
         │ • Known scenario            │
         └──────────┬──────────────────┘
                    ↓
              [Eligible?]
                    ├─ NO → MANUAL_REVIEW_REQUIRED
                    └─ YES → Continue
                            ↓
                 ┌──────────────────────┐
                 │ Step 5: Execute Fix  │
                 │ • Apply remediation  │
                 │ • Track AWS actions  │
                 └──────────┬───────────┘
                            ↓
                      [Success?]
                            ├─ YES → AUTO_REMEDIATED
                            └─ NO → FAILED
```

---

## 📊 Eligibility Scenarios

### Scenario 1: Recurring Low Severity

```
Error: Connection timeout (LOW severity)
Occurrences: 5 times in 24h
AI Candidate: false
Scenario: CONNECTION_POOL

Decision: ✅ ELIGIBLE (recurring ≥ 3)
Action: Auto-remediate
Reason: Frequent issue needs automatic handling
```

### Scenario 2: First-Time Critical Error

```
Error: Database corruption (CRITICAL severity)
Occurrences: 1 time
AI Candidate: false
Scenario: UNKNOWN

Decision: ✅ ELIGIBLE (critical severity)
Action: Auto-remediate
Reason: High severity requires immediate action
```

### Scenario 3: AI-Recommended Fix

```
Error: Lambda configuration issue (MEDIUM severity)
Occurrences: 1 time
AI Candidate: true ← AI says safe to auto-fix
Scenario: TIMEOUT

Decision: ✅ ELIGIBLE (AI candidate)
Action: Auto-remediate
Reason: AI high confidence + known pattern
```

### Scenario 4: One-Time Low Severity Unknown

```
Error: Unknown application error (LOW severity)
Occurrences: 1 time
AI Candidate: false
Scenario: UNKNOWN

Decision: ❌ NOT ELIGIBLE
Action: MANUAL_REVIEW_REQUIRED
Reason: Need human judgment for unknown issue
```

### Scenario 5: Critical Function Override

```
Error: Any error (any severity)
Function: prod-payment-processor (CRITICAL)
Recurrence: 10 times
AI Candidate: true

Decision: ❌ NOT ELIGIBLE
Action: MANUAL_APPROVAL_REQUIRED
Reason: Critical function overrides all else
```

---

## 🔧 Configuration

### Model Configuration

**File:** `src/rca_analyzer_lambda.py`

```python
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
```

**Requirements:**
- Bedrock access in us-east-1 (or your configured region)
- Claude 3.5 Sonnet model enabled
- Adequate quotas for API calls

### Recurrence Threshold

**File:** `src/enhanced_remediator_lambda.py`

```python
RECURRENCE_THRESHOLD = 3  # Number of occurrences in 24h
```

**Tuning:**
- **Lower (2):** More aggressive auto-remediation
- **Higher (5):** More conservative, requires more occurrences

### Eligibility Criteria

**Current Settings:**

```python
eligible = (
    is_recurring or           # ≥ 3 occurrences
    severity in ["HIGH", "CRITICAL"] or
    ai_candidate or           # AI recommends
    scenario != "UNKNOWN"     # Known pattern
)
```

**Customization:** Adjust in `enhanced_remediator_lambda.py`

---

## 📧 Email Notifications - Enhanced

### Email Content Now Includes:

**New Fields:**

```
AI ANALYSIS
===========
Summary: Lambda timeout error
Root Cause: Insufficient timeout configuration
Severity: MEDIUM

AI Assessment: ← NEW
• Recurrence Hint: Similar pattern seen 5 times recently
• Auto-Remediation Candidate: YES
• Rationale: High confidence timeout fix with low risk

AUTO-REMEDIATION STATUS
=======================
Eligible for Auto-Fix: YES
Eligibility Reason: ← NEW
• Recurring issue (5 occurrences in 24h)
• Known scenario: TIMEOUT
• AI recommended: YES

Action Taken: AUTO_REMEDIATED
Scenario: TIMEOUT ← NEW
Recurrence Count: 5 ← NEW
```

---

## 🧪 Testing the Intelligent System

### Test Case 1: Recurring Issue

**Objective:** Verify recurrence detection triggers auto-remediation

```bash
# Trigger same error 3 times
for i in {1..3}; do
  aws lambda invoke \
    --function-name rcra-dummy-app \
    --cli-binary-format raw-in-base64-out \
    --payload '{"scenario":"timeout"}' \
    /tmp/test-$i.json
  sleep 20
done

# Check dashboard - 3rd occurrence should auto-remediate
```

**Expected:**
- 1st occurrence: May be MANUAL_REVIEW_REQUIRED (depends on AI)
- 2nd occurrence: Still may require review
- 3rd occurrence: AUTO_REMEDIATED (recurring threshold met)

### Test Case 2: AI Candidate Recommendation

**Objective:** Verify AI recommendation triggers auto-remediation

```bash
# Trigger error that AI likely recommends
aws lambda invoke \
  --function-name rcra-dummy-app \
  --cli-binary-format raw-in-base64-out \
  --payload '{"scenario":"timeout"}' \
  /tmp/test.json

# Wait for processing
sleep 15

# Check email for AI rationale
# Should see: auto_remediation_candidate: true
```

**Expected:**
- AI analyzes: "Standard timeout issue, safe to fix"
- Sets `auto_remediation_candidate: true`
- System auto-remediates even if first occurrence

### Test Case 3: Unknown Low Severity

**Objective:** Verify manual review required for unclear issues

```bash
# Trigger unusual error
aws lambda invoke \
  --function-name rcra-dummy-app \
  --cli-binary-format raw-in-base64-out \
  --payload '{"scenario":"memory"}' \
  /tmp/test.json

# Check if first occurrence requires manual review
```

**Expected:**
- Scenario: May detect as MEMORY or UNKNOWN
- If MEMORY: Likely auto-remediate (known scenario)
- If UNKNOWN + first time + LOW: MANUAL_REVIEW_REQUIRED

### Test Case 4: High Severity Immediate Action

**Objective:** Verify high severity triggers immediate remediation

```bash
# Trigger high-severity error
# (You may need to add a high-severity scenario to dummy app)

# Expected: Immediate auto-remediation regardless of recurrence
```

---

## 📊 Monitoring & Analytics

### Key Metrics to Track

1. **Eligibility Rate**
   ```
   Eligible for Auto-Fix / Total Incidents
   Target: 60-80%
   ```

2. **Auto-Remediation Success Rate**
   ```
   AUTO_REMEDIATED / Eligible Incidents
   Target: >85%
   ```

3. **Manual Review Rate**
   ```
   MANUAL_REVIEW_REQUIRED / Total Incidents
   Target: 20-40% (depends on your environment)
   ```

4. **Recurrence Detection Accuracy**
   ```
   Recurring Issues Correctly Identified
   Target: >95%
   ```

5. **AI Recommendation Accuracy**
   ```
   AI Candidates Successfully Remediated
   Target: >90%
   ```

### Dashboard Queries

**View eligibility breakdown:**
```bash
# Check recent incidents
curl https://76ckmapns1.execute-api.us-east-1.amazonaws.com/incidents | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
total = len(data['incidents'])
eligible = sum(1 for i in data['incidents'] if i.get('remediationEligible'))
print(f'Eligible: {eligible}/{total} ({eligible/total*100:.1f}%)')
"
```

---

## 🎯 Best Practices

### For DevOps Teams

1. **Monitor Eligibility Rates**
   - If too low (<50%): Consider lowering recurrence threshold
   - If too high (>90%): Increase recurrence threshold or add more gates

2. **Review MANUAL_REVIEW_REQUIRED Cases**
   - Check why they weren't auto-remediated
   - Update patterns if needed
   - Train AI with better prompts

3. **Track AI Recommendation Accuracy**
   - If AI often wrong: Update prompt for better context
   - If AI too conservative: Adjust prompt to be more confident

4. **Tune Recurrence Threshold**
   - Staging: Lower threshold (2) for faster response
   - Production: Higher threshold (3-5) for safety

### For Support Teams

1. **Trust the AI Assessment**
   - Review `rationale` field in emails
   - AI explains why it recommended auto-fix

2. **Prioritize Manual Reviews**
   - Focus on MANUAL_REVIEW_REQUIRED cases
   - These need human judgment

3. **Monitor Recurring Issues**
   - High recurrence count = systemic problem
   - Consider permanent fix instead of auto-remediation

4. **Feedback Loop**
   - Report false positives (bad auto-fixes)
   - Report false negatives (should have auto-fixed)
   - Helps improve the system

---

## 🔐 Security Considerations

### AI Model Access

- **Principle of Least Privilege:** Only analyzer Lambda has Bedrock access
- **Model Versioning:** Pinned to specific model version
- **Audit Logging:** All Bedrock calls logged to CloudWatch

### Eligibility Gate Bypass

**Critical Functions:** Always require manual approval

```python
# Cannot be overridden by:
# - Recurrence
# - Severity
# - AI recommendation
# - Any other factor
```

### Remediation Actions

- **AWS API Calls:** All logged with before/after values
- **Rollback:** Consider implementing rollback for failed actions
- **Approval Workflow:** Can add approval step before execution

---

## 📈 ROI & Benefits

### Estimated Time Savings

**Before Intelligent Eligibility:**
- 80% of incidents auto-eligible
- Support team reviews all incidents
- Average review time: 5 minutes

**After Intelligent Eligibility:**
- 30-40% require manual review (filtered intelligently)
- Support team focuses on complex issues
- 60-70% handled automatically with confidence

**Result:**
- 50% reduction in manual review time
- Higher quality reviews (complex issues get more attention)
- Faster resolution for recurring issues

### Improved Accuracy

- **AI Reasoning:** Explains why auto-fix is safe
- **Recurrence Detection:** Identifies chronic issues
- **Pattern Recognition:** Better scenario matching
- **Risk Assessment:** Multi-factor eligibility

---

## 🚀 Future Enhancements

### Planned Improvements

1. **Machine Learning Feedback Loop**
   - Track auto-remediation outcomes
   - Feed back to improve AI prompt
   - Learn from successful patterns

2. **Custom Eligibility Rules**
   - Per-service configuration
   - Time-based rules (e.g., safer during off-peak)
   - Cost-based thresholds

3. **Advanced Recurrence Analysis**
   - Time-series pattern detection
   - Correlation with deployments
   - Seasonal/cyclical patterns

4. **Confidence Scoring**
   - AI provides confidence score (0-100%)
   - Only auto-remediate if confidence > threshold
   - Lower confidence = MANUAL_REVIEW_REQUIRED

5. **Remediation Simulation**
   - Dry-run mode before actual execution
   - Preview changes
   - Rollback capability

---

## 📚 API Reference

### Enhanced Analysis Result

```json
{
  "analysisResult": {
    "summary": "string",
    "probable_root_cause": "string",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "suggested_remediation_steps": ["string"],
    "tags": ["string"],
    "recurrence_hint": "string",
    "auto_remediation_candidate": boolean,
    "rationale": "string"
  }
}
```

### Enhanced Remediation Result

```json
{
  "remediationResult": {
    "autoRemediationEligible": boolean,
    "remediationActionTaken": "AUTO_REMEDIATED|MANUAL_REVIEW_REQUIRED|MANUAL_APPROVAL_REQUIRED|FAILED",
    "details": "string",
    "awsActions": [...],
    "scenario": "TIMEOUT|MEMORY|CONNECTION_POOL|...",
    "recurrenceCount": number,
    "eligibilityReason": "string"
  }
}
```

---

## 🎊 Summary

**RCRA v4.0 Intelligent Remediation System:**

✅ **Claude 3.5 Sonnet** - More accurate AI analysis  
✅ **Multi-Factor Eligibility** - Smarter decision making  
✅ **Recurrence Detection** - Identifies chronic issues  
✅ **Scenario Recognition** - Better pattern matching  
✅ **AI Recommendations** - Confidence-based auto-fix  
✅ **Enhanced Metadata** - Richer context for decisions  

**Result:** A truly intelligent system that knows when to auto-fix and when to ask for help! 🧠

---

**Version:** 4.0  
**Last Updated:** November 23, 2025  
**Status:** Production Ready ✅







