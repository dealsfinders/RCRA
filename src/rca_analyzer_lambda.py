import json
import os

import boto3

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

PROMPT_TEMPLATE = """
You are an SRE root cause analysis assistant.

Given the following log snippet, respond in strict JSON with fields:
- summary: short human-readable summary of the issue
- probable_root_cause: concise root cause explanation
- severity: one of LOW, MEDIUM, HIGH, CRITICAL
- suggested_remediation_steps: list of 3-5 actionable steps
- tags: array of keywords

Log:
"""  # log text appended


def handler(event, context):
    log_message = event.get("rawLogMessage", "")
    incident_id = event.get("incidentId")

    prompt = PROMPT_TEMPLATE + log_message

    body = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "max_tokens": 512,
        "temperature": 0.2,
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    model_payload = json.loads(response["body"].read().decode("utf-8"))

    text = model_payload.get("output", {}).get("message", {}).get("content", [{}])
    text = text[0].get("text", "") if text else ""

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
        }

    event["analysisResult"] = rca
    event["incidentId"] = incident_id
    return event
