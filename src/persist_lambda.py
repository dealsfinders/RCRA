import json
import os
from datetime import datetime

import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
TOPIC_ARN = os.environ["TOPIC_ARN"]

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    incident_id = event.get("incidentId")
    analysis = event.get("analysisResult", {})
    remediation = event.get("remediationResult", {})

    item = {
        "IncidentId": incident_id,
        "CreatedAt": datetime.utcnow().isoformat() + "Z",
        "LogGroup": event.get("logGroup"),
        "LogStream": event.get("logStream"),
        "RawLogMessage": event.get("rawLogMessage"),
        "AnalysisResult": analysis,
        "RemediationResult": remediation,
    }

    table.put_item(Item=item)

    subject = f"[RCRA] RCA for incident {incident_id} – {analysis.get('severity', 'UNKNOWN')}"
    steps = "\n- ".join(analysis.get("suggested_remediation_steps", []))
    message = (
        f"Incident ID: {incident_id}\n"
        f"Summary: {analysis.get('summary')}\n"
        f"Probable Root Cause: {analysis.get('probable_root_cause')}\n"
        f"Severity: {analysis.get('severity')}\n\n"
        f"Suggested Steps:\n- {steps if steps else 'None provided'}\n\n"
        f"Auto Remediation Eligible: {remediation.get('autoRemediationEligible')}"
    )

    sns.publish(TopicArn=TOPIC_ARN, Subject=subject, Message=message)

    return {"status": "saved_and_notified", "incidentId": incident_id}
