import base64
import gzip
import json
import os
from datetime import datetime
from uuid import uuid4

import boto3

sf_client = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def handler(event, context):
    cw_payload = gzip.decompress(base64.b64decode(event["awslogs"]["data"]))
    cw_json = json.loads(cw_payload)

    log_events = cw_json.get("logEvents", [])
    if not log_events:
        return {"status": "no_log_events"}

    first = log_events[0]
    message = first.get("message", "")
    log_group = cw_json.get("logGroup", "")
    log_stream = cw_json.get("logStream", "")

    incident_id = f"inc-{uuid4()}"

    input_payload = {
        "incidentId": incident_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "logGroup": log_group,
        "logStream": log_stream,
        "rawLogMessage": message,
    }

    sf_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=json.dumps(input_payload),
    )

    return {"status": "started", "incidentId": incident_id}
