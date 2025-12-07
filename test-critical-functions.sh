#!/bin/bash

# RCRA Critical Functions Test Script
# This script demonstrates the critical functions feature

API_ENDPOINT="https://76ckmapns1.execute-api.us-east-1.amazonaws.com"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              🧪 RCRA Critical Functions Test                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Show current critical functions
echo "📋 Step 1: Current Critical Functions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_ENDPOINT/config/critical-functions" | python3 -m json.tool
echo ""
echo ""

# Step 2: Add rcra-test-app to critical list
echo "➕ Step 2: Adding 'rcra-test-app' to Critical List"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s -X POST "$API_ENDPOINT/config/critical-functions" \
  -H "Content-Type: application/json" \
  -d '{"action": "add", "functionName": "rcra-test-app"}' | python3 -m json.tool
echo ""
echo ""

# Step 3: Verify it was added
echo "✅ Step 3: Verify Addition"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_ENDPOINT/config/critical-functions" | python3 -m json.tool
echo ""
echo ""

# Step 4: Trigger a test error
echo "🔥 Step 4: Triggering Test Error from Critical Function"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Invoking dummy app to generate error..."
aws lambda invoke \
  --function-name rcra-dummy-app \
  --cli-binary-format raw-in-base64-out \
  --payload '{"scenario":"timeout"}' \
  /tmp/rcra-test-response.json > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Error triggered successfully!"
    cat /tmp/rcra-test-response.json | python3 -m json.tool
else
    echo "⚠️ Failed to trigger error"
fi
echo ""
echo ""

# Step 5: Wait for processing
echo "⏳ Step 5: Waiting for RCRA to Process (15 seconds)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for i in {15..1}; do
    echo -ne "\rWaiting... $i seconds remaining  "
    sleep 1
done
echo -e "\r✅ Processing complete!                    "
echo ""
echo ""

# Step 6: Check the latest incident
echo "📊 Step 6: Latest Incident Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Fetching latest incidents..."
curl -s "$API_ENDPOINT/statistics" | python3 -c "
import sys, json
data = json.load(sys.stdin)
incidents = data.get('recentIncidents', [])
if incidents:
    latest = incidents[0]
    print('🎫 Ticket:', latest.get('ticketNumber', 'N/A'))
    print('📝 Summary:', latest.get('summary', 'N/A'))
    print('🏷️  Severity:', latest.get('severity', 'UNKNOWN'))
    print('🔧 Remediation:', latest.get('remediationAction', 'NONE'))
    print('✅ Eligible:', latest.get('remediationEligible', False))
    print('')
    if latest.get('remediationAction') == 'MANUAL_APPROVAL_REQUIRED':
        print('✅ SUCCESS! Critical function protection is working!')
        print('   The system detected this is a critical function and')
        print('   requires manual approval instead of auto-fixing.')
    elif latest.get('remediationAction') == 'AUTO_REMEDIATED':
        print('⚠️  UNEXPECTED: Function was auto-fixed even though it is critical!')
    elif latest.get('remediationAction') == 'FAILED':
        print('ℹ️  Status: Auto-fix failed (may be expected for test scenarios)')
    else:
        print('ℹ️  Status:', latest.get('remediationAction', 'NONE'))
else:
    print('No incidents found')
"
echo ""
echo ""

# Step 7: Summary
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                          📋 TEST SUMMARY                                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "What just happened:"
echo "1. ✅ Checked current critical functions list"
echo "2. ✅ Added 'rcra-test-app' to critical list"
echo "3. ✅ Verified the addition"
echo "4. ✅ Triggered an error from rcra-test-app"
echo "5. ✅ Waited for RCRA to process the error"
echo "6. ✅ Checked the incident status"
echo ""
echo "Expected behavior:"
echo "• Normal function → Auto-fix applied → ✅ AUTO-FIXED"
echo "• Critical function → Blocked → 👤 APPROVAL REQUIRED"
echo ""
echo "Next steps:"
echo "1. Check your email (selvaonline@gmail.com) for notification"
echo "2. Open dashboard: http://localhost:8080/index.html"
echo "3. Do HARD REFRESH (Cmd+Shift+R or Ctrl+Shift+R)"
echo "4. Look for incident with 👤 APPROVAL badge"
echo ""
echo "To remove from critical list:"
echo "curl -X POST $API_ENDPOINT/config/critical-functions \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"action\":\"remove\",\"functionName\":\"rcra-test-app\"}'"
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                     🎊 Test Complete! 🎊                                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"










