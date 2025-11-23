import json
import os
import random
from datetime import datetime

import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
TOPIC_ARN = os.environ["TOPIC_ARN"]

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

table = dynamodb.Table(TABLE_NAME)


def generate_ticket_number():
    """Generate a human-friendly support ticket number like RCRA-2025-001234"""
    year = datetime.utcnow().year
    # Generate a random 6-digit number
    ticket_num = random.randint(100000, 999999)
    return f"RCRA-{year}-{ticket_num}"


def track_error_frequency(error_signature, log_group):
    """
    Track how many times similar errors have occurred in the last 24 hours
    Returns count and timestamps of occurrences
    """
    try:
        from datetime import timedelta
        from boto3.dynamodb.conditions import Attr
        
        # Calculate 24 hours ago
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_24h_str = last_24h.isoformat() + "Z"
        
        # Scan for similar errors in last 24 hours
        response = table.scan(
            FilterExpression=Attr('ErrorSignature').eq(error_signature) & 
                           Attr('CreatedAt').gt(last_24h_str) &
                           Attr('LogGroup').eq(log_group)
        )
        
        items = response.get('Items', [])
        occurrences = []
        
        for item in items:
            occurrences.append({
                'timestamp': item.get('CreatedAt'),
                'incidentId': item.get('IncidentId'),
                'ticketNumber': item.get('TicketNumber'),
                'status': item.get('Status', 'UNKNOWN')
            })
        
        # Sort by timestamp descending
        occurrences.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'count': len(occurrences),
            'occurrences': occurrences[:10],  # Last 10 occurrences
            'signature': error_signature
        }
    except Exception as e:
        print(f"[ERROR] Failed to track error frequency: {str(e)}")
        return {
            'count': 1,
            'occurrences': [],
            'signature': error_signature
        }


def handler(event, context):
    incident_id = event.get("incidentId")
    
    # Handle nested structure from Step Functions
    # The event has analysis.analysisResult and remediation.remediationResult
    analysis_wrapper = event.get("analysis", {})
    remediation_wrapper = event.get("remediation", {})
    
    analysis = analysis_wrapper.get("analysisResult", {})
    remediation = remediation_wrapper.get("remediationResult", {})
    
    # Generate human-friendly ticket number
    ticket_number = generate_ticket_number()
    
    # Determine ticket status based on remediation result
    remediation_action = remediation.get('remediationActionTaken', 'NONE')
    if remediation_action == "AUTO_REMEDIATED":
        status = "RESOLVED"
        resolved_at = datetime.utcnow().isoformat() + "Z"
        resolved_by = "SYSTEM_AUTO_REMEDIATION"
    else:
        status = "OPEN"
        resolved_at = None
        resolved_by = None
    
    # Create error signature for frequency tracking (use summary as signature)
    error_summary = analysis.get('summary', 'Unknown error')
    error_signature = error_summary[:100]  # Use first 100 chars as signature

    item = {
        "IncidentId": incident_id,
        "TicketNumber": ticket_number,
        "Status": status,  # OPEN or RESOLVED
        "ResolvedAt": resolved_at,
        "ResolvedBy": resolved_by,
        "CreatedAt": datetime.utcnow().isoformat() + "Z",
        "LogGroup": event.get("logGroup"),
        "LogStream": event.get("logStream"),
        "RawLogMessage": event.get("rawLogMessage"),
        "AnalysisResult": analysis,
        "RemediationResult": remediation,
        "ErrorSignature": error_signature,  # For frequency tracking
    }

    table.put_item(Item=item)
    
    # Track error frequency (check for similar errors in last 24 hours)
    error_occurrences = track_error_frequency(error_signature, event.get("logGroup"))
    print(f"[PERSIST] Error signature: {error_signature}")
    print(f"[PERSIST] Occurrences in last 24h: {error_occurrences['count']}")

    # Determine email subject based on remediation status
    severity = analysis.get('severity', 'UNKNOWN')
    remediation_action = remediation.get('remediationActionTaken', 'NONE')
    
    if remediation_action == 'AUTO_REMEDIATED':
        subject = f"[RCRA] ✅ AUTO-FIXED: {severity} - {incident_id}"
    elif remediation_action == 'FAILED':
        subject = f"[RCRA] ⚠️ AUTO-FIX FAILED: {severity} - {incident_id}"
    elif remediation_action == 'MANUAL_APPROVAL_REQUIRED':
        subject = f"[RCRA] 👤 APPROVAL NEEDED: {severity} - {incident_id}"
    else:
        subject = f"[RCRA] 📊 NEW INCIDENT: {severity} - {incident_id}"

    # Build detailed message with error frequency info
    message = build_email_message(incident_id, ticket_number, event, analysis, remediation, error_occurrences, status)

    sns.publish(TopicArn=TOPIC_ARN, Subject=subject, Message=message)

    return {"status": "saved_and_notified", "incidentId": incident_id, "ticketNumber": ticket_number}


def build_email_message(incident_id, ticket_number, event, analysis, remediation, error_occurrences, status):
    """Build a detailed email message with remediation information"""
    
    # Header
    message = f"""
╔══════════════════════════════════════════════════════════════════╗
║          RCRA - Root Cause & Remediation Alert                   ║
╚══════════════════════════════════════════════════════════════════╝

INCIDENT DETAILS
================
Support Ticket: {ticket_number}
Ticket Status: {status}
Incident ID: {incident_id}
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Severity: {analysis.get('severity', 'UNKNOWN')}
Log Group: {event.get('logGroup')}
Log Stream: {event.get('logStream')}

ERROR FREQUENCY
===============
This error occurred {error_occurrences['count']} time(s) in the last 24 hours.
"""
    
    # Add recent occurrences if there are multiple
    if error_occurrences['count'] > 1:
        message += "\nRecent Occurrences:\n"
        for occ in error_occurrences['occurrences'][:5]:
            message += f"  • {occ['timestamp']} - Ticket: {occ.get('ticketNumber', 'N/A')} ({occ.get('status', 'UNKNOWN')})\n"
    
    message += "\n"

    # Analysis Section
    message += f"""
AI ANALYSIS
===========
Summary: {analysis.get('summary', 'N/A')}

Root Cause:
{analysis.get('probable_root_cause', 'N/A')}

"""

    # Remediation Section
    auto_remediation = remediation.get('autoRemediationEligible', False)
    action_taken = remediation.get('remediationActionTaken', 'NONE')
    details = remediation.get('details', '')
    aws_actions = remediation.get('awsActions', [])

    message += f"""
AUTO-REMEDIATION STATUS
=======================
Eligible for Auto-Fix: {'YES' if auto_remediation else 'NO'}
Action Taken: {action_taken}

"""

    if action_taken == 'AUTO_REMEDIATED':
        message += f"""✅ SUCCESSFULLY AUTO-REMEDIATED!

Details: {details}

AWS Actions Performed:
"""
        for action in aws_actions:
            message += f"""
  • Service: {action.get('service', 'N/A')}
  • Action: {action.get('action', 'N/A')}
  • Resource: {action.get('resource', 'N/A')}
  • Changes: {json.dumps(action.get('changes', {}), indent=4)}
"""
        message += "\n✨ The issue has been automatically resolved. No manual intervention needed."

    elif action_taken == 'FAILED':
        message += f"""⚠️ AUTO-REMEDIATION FAILED

Details: {details}

Manual intervention is required. Please review the incident in the dashboard.
"""

    elif action_taken == 'MANUAL_APPROVAL_REQUIRED':
        message += f"""👤 MANUAL APPROVAL REQUIRED

Details: {details}

This is a critical function that requires human approval before remediation.
Please review and approve the suggested actions in the dashboard.
"""

    elif action_taken == 'ANALYSIS_ONLY':
        message += f"""📊 ANALYSIS COMPLETED

Details: {details}

No automatic remediation was performed. Please review the suggested steps below.
"""

    else:
        message += f"""
No automatic remediation was attempted.
"""

    # Suggested Remediation Steps
    steps = analysis.get("suggested_remediation_steps", [])
    if steps:
        message += f"""

SUGGESTED REMEDIATION STEPS (from AI Analysis)
===============================================
"""
        for i, step in enumerate(steps, 1):
            message += f"{i}. {step}\n"

    # Tags
    tags = analysis.get("tags", [])
    if tags:
        message += f"""
Tags: {', '.join(tags)}
"""

    # Error Log
    raw_message = event.get('rawLogMessage', '')
    if raw_message:
        message += f"""

RAW ERROR LOG
=============
{raw_message[:500]}{'...' if len(raw_message) > 500 else ''}

"""

    # Footer
    message += f"""
══════════════════════════════════════════════════════════════════
View full details in the RCRA Dashboard:
http://localhost:8080/index.html

Need help? Check the documentation:
/Users/selva/Documents/Project/RCRA/AUTO_REMEDIATION_GUIDE.md
══════════════════════════════════════════════════════════════════
"""

    return message
