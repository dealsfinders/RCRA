import json
import os

import boto3

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

PROMPT_TEMPLATE = """
You are an SRE root cause analysis assistant.

Given the following log snippet, respond in strict JSON with fields:
- summary: short human-readable summary of the issue
- probable_root_cause: concise root cause explanation
- severity: one of LOW, MEDIUM, HIGH, CRITICAL
- suggested_remediation_steps: list of 3-5 actionable steps
- tags: array of keywords
- recurrence_hint: boolean, true if this looks like a recurring/systemic issue
- auto_remediation_candidate: boolean, true if safe/appropriate to attempt auto remediation
- rationale: short sentence explaining the recurrence/eligibility decision

Log:
"""  # log text appended


def handler(event, context):
    log_message = event.get("rawLogMessage", "")
    incident_id = event.get("incidentId")

    prompt = PROMPT_TEMPLATE + log_message

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800,
        "temperature": 0.1,
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    model_payload = json.loads(response["body"].read().decode("utf-8"))

    # Extract text from Claude response
    content = model_payload.get("content", [])
    text = content[0].get("text", "") if content else ""

    try:
        rca = json.loads(text)
    except json.JSONDecodeError:
        rca = {
            "summary": text[:200],
            "probable_root_cause": "Model returned non-JSON text.",
            "severity": "MEDIUM",
            "suggested_remediation_steps": [
                "Review full logs in CloudWatch.",
                "Refine RCA prompt and retry.",
            ],
            "tags": ["fallback"],
            "recurrence_hint": False,
            "auto_remediation_candidate": False,
            "rationale": "Fallback – model did not return JSON.",
        }

    event["analysisResult"] = rca
    event["incidentId"] = incident_id
    return event
