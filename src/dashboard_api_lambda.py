import json
import os
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME", "RCRARootCauseTable")
table = dynamodb.Table(table_name)
topic_arn = os.environ.get("TOPIC_ARN")
sns = boto3.client("sns") if topic_arn else None
logs_client = boto3.client("logs")


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal to JSON"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


lambda_client = boto3.client("lambda")


def cors_headers():
    """Return CORS headers for API responses"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }


def publish_stage_notification(stage, item, status, details=""):
    """Publish an SNS notification for a ticket stage transition"""
    if not sns or not topic_arn:
        return

    incident_id = item.get("IncidentId")
    ticket = item.get("TicketNumber", "N/A")
    analysis = item.get("AnalysisResult", {})
    remediation = item.get("RemediationResult", {})

    summary = analysis.get("summary", "No summary provided")
    severity = analysis.get("severity", "UNKNOWN")
    action_taken = remediation.get("remediationActionTaken", "N/A")

    subject = f"[RCRA] {stage}: {severity} - {incident_id}"

    message = (
        f"Incident: {incident_id}\n"
        f"Ticket: {ticket}\n"
        f"Status: {status}\n"
        f"Severity: {severity}\n"
        f"Summary: {summary}\n"
        f"Remediation action: {action_taken}\n"
        f"Details: {details}\n"
        f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
    )

    try:
        sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
    except Exception as e:
        print(f"[WARN] Failed to publish stage notification: {str(e)}")


def handler(event, context):
    """
    API Gateway Lambda handler for RCRA Dashboard
    Routes:
    - GET /incidents - List all incidents with pagination
    - GET /incidents/{id} - Get specific incident details
    - GET /statistics - Get system statistics
    """

    # Support both API Gateway v1 and v2 formats
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("path") or event.get("rawPath", "")
    path_parameters = event.get("pathParameters") or {}
    query_parameters = event.get("queryStringParameters") or {}

    # Debug logging
    print(f"Event: {json.dumps(event)}")
    print(f"HTTP Method: {http_method}, Path: {path}")

    # Handle OPTIONS for CORS
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({"message": "OK"}),
        }

    try:
        # Route to appropriate handler
        if path == "/incidents" or path.endswith("/incidents"):
            response_data = get_incidents(query_parameters)
        elif "/incidents/" in path and path_parameters.get("id"):
            if path.endswith("/logs"):
                response_data = get_incident_logs(path_parameters["id"], query_parameters)
            else:
                response_data = get_incident_by_id(path_parameters["id"])
        elif path == "/statistics" or path.endswith("/statistics"):
            response_data = get_statistics()
        elif path == "/trigger-error" or path.endswith("/trigger-error"):
            response_data = trigger_dummy_error(query_parameters)
        elif (path == "/remediate" or path.endswith("/remediate")) and http_method == "POST":
            body = json.loads(event.get("body", "{}"))
            response_data = trigger_remediation(body)
        elif path == "/config/critical-functions" or path.endswith("/config/critical-functions"):
            if http_method == "GET":
                response_data = get_critical_functions()
            elif http_method == "POST":
                body = json.loads(event.get("body", "{}"))
                response_data = update_critical_functions(body)
            else:
                return {
                    "statusCode": 405,
                    "headers": cors_headers(),
                    "body": json.dumps({"error": "Method not allowed"}),
                }
        elif path == "/config/auto-remediation" or path.endswith("/config/auto-remediation"):
            if http_method == "GET":
                response_data = get_auto_remediation_config()
            elif http_method == "POST":
                body = json.loads(event.get("body", "{}"))
                response_data = update_auto_remediation_config(body)
            else:
                return {
                    "statusCode": 405,
                    "headers": cors_headers(),
                    "body": json.dumps({"error": "Method not allowed"}),
                }
        elif path == "/resolve" or path.endswith("/resolve"):
            if http_method == "POST":
                body = json.loads(event.get("body", "{}"))
                incident_id = body.get("incidentId")
                resolved_by = body.get("resolvedBy", "MANUAL_RESOLUTION")
                response_data = resolve_incident(incident_id, resolved_by)
            else:
                return {
                    "statusCode": 405,
                    "headers": cors_headers(),
                    "body": json.dumps({"error": "Method not allowed"}),
                }
        else:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Route not found"}),
            }

        return {
            "statusCode": 200,
            "headers": {**cors_headers(), "Content-Type": "application/json"},
            "body": json.dumps(response_data, cls=DecimalEncoder),
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def get_incidents(query_params):
    """Get list of incidents with optional filtering and pagination"""
    limit = int(query_params.get("limit", 50))
    last_key = query_params.get("lastKey")

    scan_kwargs = {"Limit": limit}

    if last_key:
        scan_kwargs["ExclusiveStartKey"] = {"IncidentId": last_key}

    # Filter by severity if provided
    severity = query_params.get("severity")
    if severity:
        scan_kwargs["FilterExpression"] = Attr("AnalysisResult.severity").eq(severity)

    response = table.scan(**scan_kwargs)

    items = response.get("Items", [])
    
    # Filter out configuration items (CONFIG_*)
    items = [item for item in items if not item.get("IncidentId", "").startswith("CONFIG_")]

    # Sort by CreatedAt descending
    items.sort(key=lambda x: x.get("CreatedAt", ""), reverse=True)

    # Parse and flatten data for easier frontend consumption
    incidents = []
    for item in items:
        analysis = item.get("AnalysisResult", {})
        remediation = item.get("RemediationResult", {})
        
        # Get error frequency for this signature
        error_signature = item.get("ErrorSignature", "")
        error_count = get_error_frequency_count(error_signature, item.get("LogGroup"))
        
        incident = {
            "incidentId": item.get("IncidentId"),
            "ticketNumber": item.get("TicketNumber", "N/A"),
            "status": item.get("Status", "OPEN"),
            "resolvedAt": item.get("ResolvedAt"),
            "resolvedBy": item.get("ResolvedBy"),
            "timestamp": item.get("CreatedAt"),
            "logGroup": item.get("LogGroup"),
            "logStream": item.get("LogStream"),
            "rawMessage": item.get("RawLogMessage", "")[:200],  # Truncate for list view
            "summary": analysis.get("summary", "N/A"),
            "severity": analysis.get("severity", "UNKNOWN"),
            "rootCause": analysis.get("probable_root_cause", "N/A"),
            "tags": analysis.get("tags", []),
            "remediationEligible": remediation.get("autoRemediationEligible", False),
            "remediationAction": remediation.get("remediationActionTaken", "NONE"),
            "errorSignature": error_signature,
            "occurrenceCount": error_count,
        }
        incidents.append(incident)

    result = {
        "incidents": incidents,
        "count": len(incidents),
        "lastKey": response.get("LastEvaluatedKey", {}).get("IncidentId"),
    }

    return result


def get_incident_by_id(incident_id):
    """Get detailed information about a specific incident"""
    response = table.get_item(Key={"IncidentId": incident_id})

    item = response.get("Item")
    if not item:
        return {"error": "Incident not found"}

    # Return full incident details
    analysis = item.get("AnalysisResult", {})
    remediation = item.get("RemediationResult", {})
    error_signature = item.get("ErrorSignature") or analysis.get("summary", "")[:100]
    log_group = item.get("LogGroup")
    related = get_error_occurrences(error_signature, log_group)
    related = [r for r in related if r.get("incidentId") != incident_id]

    incident_detail = {
        "incidentId": item.get("IncidentId"),
        "ticketNumber": item.get("TicketNumber", "N/A"),
        "status": item.get("Status", "OPEN"),
        "resolvedAt": item.get("ResolvedAt"),
        "resolvedBy": item.get("ResolvedBy"),
        "timestamp": item.get("CreatedAt"),
        "logGroup": item.get("LogGroup"),
        "logStream": item.get("LogStream"),
        "rawMessage": item.get("RawLogMessage", ""),
        "errorSignature": error_signature,
        "analysis": {
            "summary": analysis.get("summary", "N/A"),
            "severity": analysis.get("severity", "UNKNOWN"),
            "rootCause": analysis.get("probable_root_cause", "N/A"),
            "remediationSteps": analysis.get("suggested_remediation_steps", []),
            "tags": analysis.get("tags", []),
        },
        "remediation": {
            "eligible": remediation.get("autoRemediationEligible", False),
            "actionTaken": remediation.get("remediationActionTaken", "NONE"),
            "details": remediation.get("details", ""),
            "awsActions": remediation.get("awsActions", []),
        },
        "relatedIncidents": related,
    }

    return incident_detail


def get_incident_logs(incident_id, query_params):
    """Fetch recent log events for the incident's log group/stream"""
    limit = int(query_params.get("limit", 50))
    try:
        # Fetch incident to get log metadata
        response = table.get_item(Key={"IncidentId": incident_id})
        item = response.get("Item")
        if not item:
            return {"error": "Incident not found"}

        log_group = item.get("LogGroup")
        log_stream = item.get("LogStream")
        if not log_group:
            return {"error": "Log group not recorded for this incident"}

        params = {
            "logGroupName": log_group,
            "limit": limit,
        }
        if log_stream:
            params["logStreamNames"] = [log_stream]

        res = logs_client.filter_log_events(**params)
        events = res.get("events", [])
        # Normalize shape
        parsed = [
            {
                "timestamp": evt.get("timestamp"),
                "ingestionTime": evt.get("ingestionTime"),
                "message": evt.get("message"),
                "logStreamName": evt.get("logStreamName"),
            }
            for evt in events
        ]
        return {"events": parsed, "count": len(parsed)}
    except Exception as e:
        print(f"[LOGS] Failed to fetch logs: {str(e)}")
        return {"error": str(e)}


def get_statistics():
    """Calculate and return system statistics"""
    # Scan all items (in production, consider using DynamoDB Streams or separate stats table)
    response = table.scan()
    items = response.get("Items", [])
    
    # Filter out configuration items (CONFIG_*)
    items = [item for item in items if not item.get("IncidentId", "").startswith("CONFIG_")]

    # Calculate statistics
    total_incidents = len(items)
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    status_counts = {"OPEN": 0, "RESOLVED": 0}
    remediation_eligible = 0
    recent_incidents = []

    # Get date for last 24 hours
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    incidents_24h = 0

    all_tags = {}

    for item in items:
        analysis = item.get("AnalysisResult", {})
        severity = analysis.get("severity", "UNKNOWN")
        if severity in severity_counts:
            severity_counts[severity] += 1
        
        # Count status
        status = item.get("Status", "OPEN")
        if status in status_counts:
            status_counts[status] += 1

        # Count remediation eligible
        remediation = item.get("RemediationResult", {})
        if remediation.get("autoRemediationEligible", False):
            remediation_eligible += 1

        # Count last 24h incidents
        created_at = item.get("CreatedAt", "")
        if created_at:
            try:
                incident_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if incident_time.replace(tzinfo=None) > last_24h:
                    incidents_24h += 1
            except:
                pass

        # Aggregate tags
        tags = analysis.get("tags", [])
        for tag in tags:
            all_tags[tag] = all_tags.get(tag, 0) + 1

    # Get top 10 tags
    top_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10]

    # Get 5 most recent incidents
    items.sort(key=lambda x: x.get("CreatedAt", ""), reverse=True)
    for item in items[:5]:
        analysis = item.get("AnalysisResult", {})
        remediation = item.get("RemediationResult", {})
        recent_incidents.append(
            {
                "incidentId": item.get("IncidentId"),
                "ticketNumber": item.get("TicketNumber", "N/A"),
                "status": item.get("Status", "OPEN"),
                "timestamp": item.get("CreatedAt"),
                "summary": analysis.get("summary", "N/A"),
                "severity": analysis.get("severity", "UNKNOWN"),
                "remediationAction": remediation.get("remediationActionTaken", "NONE"),
                "remediationEligible": remediation.get("autoRemediationEligible", False),
            }
        )

    statistics = {
        "overview": {
            "totalIncidents": total_incidents,
            "incidents24h": incidents_24h,
            "remediationEligible": remediation_eligible,
            "avgSeverity": _calculate_avg_severity(severity_counts, total_incidents),
            "openTickets": status_counts.get("OPEN", 0),
            "resolvedTickets": status_counts.get("RESOLVED", 0),
        },
        "severityBreakdown": severity_counts,
        "statusBreakdown": status_counts,
        "topTags": [{"tag": tag, "count": count} for tag, count in top_tags],
        "recentIncidents": recent_incidents,
        "lastUpdated": datetime.utcnow().isoformat() + "Z",
    }

    return statistics


def _calculate_avg_severity(severity_counts, total):
    """Calculate weighted average severity"""
    if total == 0:
        return "N/A"

    severity_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}

    weighted_sum = sum(
        severity_counts.get(sev, 0) * weight for sev, weight in severity_weights.items()
    )

    avg_weight = weighted_sum / total if total > 0 else 0

    if avg_weight >= 3.5:
        return "CRITICAL"
    elif avg_weight >= 2.5:
        return "HIGH"
    elif avg_weight >= 1.5:
        return "MEDIUM"
    else:
        return "LOW"


def trigger_dummy_error(query_params):
    """Trigger the dummy application to generate an error"""
    scenario = query_params.get("scenario", "random")
    
    try:
        # Invoke dummy app Lambda
        response = lambda_client.invoke(
            FunctionName="rcra-dummy-app",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "queryStringParameters": {"scenario": scenario}
            })
        )
        
        payload = json.loads(response["Payload"].read())
        
        return {
            "success": True,
            "scenario": scenario,
            "message": f"Triggered {scenario} error scenario",
            "response": payload,
            "note": "Check CloudWatch logs /aws/lambda/rcra-dummy-app for the error"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to trigger error scenario"
        }


def trigger_remediation(body):
    """Manually trigger remediation for an incident"""
    incident_id = body.get("incidentId")
    action = body.get("action")  # e.g., "restart", "increase_timeout", "increase_memory", "approve_and_remediate"
    triggered_by = body.get("triggeredBy", "DASHBOARD_MANUAL_REMEDIATION")
    approved = body.get("approved", False)
    
    if not incident_id:
        return {"error": "incidentId is required"}
    
    try:
        # Get incident details
        response = table.get_item(Key={"IncidentId": incident_id})
        item = response.get("Item")
        
        if not item:
            return {"error": "Incident not found"}
        
        log_group = item.get("LogGroup", "")
        raw_message = item.get("RawLogMessage", "").lower()
        current_remediation = item.get("RemediationResult", {})
        scenario = current_remediation.get("scenario", "general")
        
        # If this is an approval action, perform actual remediation
        if action == "approve_and_remediate" and approved:
            remediation_result = perform_approved_remediation(log_group, raw_message, scenario, item)
            
            # Determine final status based on remediation result
            final_status = "RESOLVED" if remediation_result.get("success") else "OPEN"
            action_taken = remediation_result.get("actionTaken", "APPROVED_REMEDIATION_ATTEMPTED")
            
            remediation_update = {
                "autoRemediationEligible": True,
                "remediationActionTaken": action_taken,
                "details": remediation_result.get("details", "Approved remediation executed"),
                "awsActions": remediation_result.get("awsActions", []),
                "approvedBy": triggered_by,
                "approvedAt": datetime.utcnow().isoformat() + "Z",
                "scenario": scenario,
            }
            
            update_expression = "SET RemediationResult = :rem, #status = :status"
            expression_values = {
                ":rem": remediation_update,
                ":status": final_status,
            }
            
            if final_status == "RESOLVED":
                update_expression += ", ResolvedAt = :resolvedAt, ResolvedBy = :resolvedBy"
                expression_values[":resolvedAt"] = datetime.utcnow().isoformat() + "Z"
                expression_values[":resolvedBy"] = triggered_by
            
            table.update_item(
                Key={"IncidentId": incident_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={"#status": "Status"},
                ExpressionAttributeValues=expression_values,
            )
            
            # Send notification
            item["RemediationResult"] = remediation_update
            item["Status"] = final_status
            publish_stage_notification(
                stage="Approved Remediation Complete" if final_status == "RESOLVED" else "Remediation Attempted",
                item=item,
                status=final_status,
                details=remediation_update["details"],
            )
            
            return {
                "success": remediation_result.get("success", True),
                "incidentId": incident_id,
                "action": action_taken,
                "status": final_status,
                "message": remediation_result.get("details", "Approved remediation executed"),
                "awsActions": remediation_result.get("awsActions", []),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        # Standard manual trigger (non-approval flow)
        remediation_action = (action or "MANUAL_TRIGGERED").upper()
        remediation_update = {
            "autoRemediationEligible": True,
            "remediationActionTaken": f"{remediation_action}_IN_PROGRESS",
            "details": f"Remediation triggered via dashboard action '{action or 'manual'}' and is now IN_PROGRESS.",
            "awsActions": item.get("RemediationResult", {}).get("awsActions", []),
            "manualTrigger": True,
        }

        table.update_item(
            Key={"IncidentId": incident_id},
            UpdateExpression="SET RemediationResult = :rem, #status = :status",
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={
                ":rem": remediation_update,
                ":status": "IN_PROGRESS",
            },
        )

        # Send notification for IN_PROGRESS stage
        item["RemediationResult"] = remediation_update
        item["Status"] = "IN_PROGRESS"
        publish_stage_notification(
            stage="Remediation In Progress",
            item=item,
            status="IN_PROGRESS",
            details=remediation_update["details"],
        )
        
        return {
            "success": True,
            "incidentId": incident_id,
            "action": action,
            "status": "IN_PROGRESS",
            "message": f"Remediation action '{action}' started for incident {incident_id}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def perform_approved_remediation(log_group, raw_message, scenario, item):
    """Perform actual remediation after approval"""
    # Extract function name from log group
    function_name = log_group.replace("/aws/lambda/", "") if log_group.startswith("/aws/lambda/") else None
    
    if not function_name:
        return {
            "success": False,
            "actionTaken": "APPROVED_BUT_NO_FUNCTION",
            "details": "Could not extract function name from log group for remediation",
            "awsActions": []
        }
    
    try:
        # Determine remediation based on scenario/error type
        if scenario == "lambdaTimeout" or "timeout" in raw_message:
            return remediate_timeout_approved(function_name)
        elif scenario == "outOfMemory" or "memory" in raw_message:
            return remediate_memory_approved(function_name)
        elif scenario == "connectionPool" or ("connection" in raw_message and "pool" in raw_message):
            return remediate_connection_pool_approved(function_name)
        else:
            # Generic restart for unknown scenarios
            return remediate_restart_approved(function_name)
            
    except Exception as e:
        return {
            "success": False,
            "actionTaken": "APPROVED_REMEDIATION_FAILED",
            "details": f"Remediation failed: {str(e)}",
            "awsActions": []
        }


def remediate_timeout_approved(function_name):
    """Increase Lambda timeout after approval"""
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        current_timeout = response['Timeout']
        new_timeout = min(current_timeout * 2, 900)
        
        if new_timeout > current_timeout:
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Timeout=new_timeout
            )
            return {
                "success": True,
                "actionTaken": "APPROVED_AUTO_REMEDIATED",
                "details": f"✅ Approved: Increased Lambda timeout from {current_timeout}s to {new_timeout}s",
                "awsActions": [{
                    "service": "lambda",
                    "action": "update_function_configuration",
                    "resource": function_name,
                    "changes": {"timeout_before": current_timeout, "timeout_after": new_timeout}
                }]
            }
        else:
            return {
                "success": True,
                "actionTaken": "APPROVED_LIMIT_REACHED",
                "details": f"Timeout already at maximum ({current_timeout}s). Manual optimization needed.",
                "awsActions": []
            }
    except Exception as e:
        return {
            "success": False,
            "actionTaken": "APPROVED_REMEDIATION_FAILED",
            "details": f"Failed to increase timeout: {str(e)}",
            "awsActions": []
        }


def remediate_memory_approved(function_name):
    """Increase Lambda memory after approval"""
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        current_memory = response['MemorySize']
        new_memory = min(current_memory * 2, 10240)
        
        if new_memory > current_memory:
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                MemorySize=new_memory
            )
            return {
                "success": True,
                "actionTaken": "APPROVED_AUTO_REMEDIATED",
                "details": f"✅ Approved: Increased Lambda memory from {current_memory}MB to {new_memory}MB",
                "awsActions": [{
                    "service": "lambda",
                    "action": "update_function_configuration",
                    "resource": function_name,
                    "changes": {"memory_before": current_memory, "memory_after": new_memory}
                }]
            }
        else:
            return {
                "success": True,
                "actionTaken": "APPROVED_LIMIT_REACHED",
                "details": f"Memory already at maximum ({current_memory}MB). Manual optimization needed.",
                "awsActions": []
            }
    except Exception as e:
        return {
            "success": False,
            "actionTaken": "APPROVED_REMEDIATION_FAILED",
            "details": f"Failed to increase memory: {str(e)}",
            "awsActions": []
        }


def remediate_connection_pool_approved(function_name):
    """Restart Lambda to reset connection pool after approval"""
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = response.get('Environment', {}).get('Variables', {})
        env_vars['APPROVED_RESTART'] = datetime.utcnow().isoformat()
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        return {
            "success": True,
            "actionTaken": "APPROVED_AUTO_REMEDIATED",
            "details": f"✅ Approved: Restarted Lambda {function_name} to reset connection pool",
            "awsActions": [{
                "service": "lambda",
                "action": "restart_function",
                "resource": function_name,
                "changes": {"method": "environment_variable_update", "timestamp": datetime.utcnow().isoformat()}
            }]
        }
    except Exception as e:
        return {
            "success": False,
            "actionTaken": "APPROVED_REMEDIATION_FAILED",
            "details": f"Failed to restart Lambda: {str(e)}",
            "awsActions": []
        }


def remediate_restart_approved(function_name):
    """Generic Lambda restart after approval"""
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = response.get('Environment', {}).get('Variables', {})
        env_vars['APPROVED_RESTART'] = datetime.utcnow().isoformat()
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        return {
            "success": True,
            "actionTaken": "APPROVED_AUTO_REMEDIATED",
            "details": f"✅ Approved: Restarted Lambda {function_name}",
            "awsActions": [{
                "service": "lambda",
                "action": "restart_function",
                "resource": function_name,
                "changes": {"method": "environment_variable_update"}
            }]
        }
    except Exception as e:
        return {
            "success": False,
            "actionTaken": "APPROVED_REMEDIATION_FAILED",
            "details": f"Failed to restart Lambda: {str(e)}",
            "awsActions": []
        }


def get_critical_functions():
    """Get the list of critical functions that require manual approval"""
    try:
        response = table.get_item(Key={"IncidentId": "CONFIG_CRITICAL_FUNCTIONS"})
        item = response.get("Item", {})
        functions = item.get("functions", [])
        
        return {
            "success": True,
            "criticalFunctions": functions,
            "count": len(functions)
        }
    except Exception as e:
        return {
            "success": True,
            "criticalFunctions": [],
            "count": 0
        }


def update_critical_functions(body):
    """Update the list of critical functions"""
    functions = body.get("functions", [])
    action = body.get("action")  # "add" or "remove"
    function_name = body.get("functionName")
    
    try:
        # Get current list
        response = table.get_item(Key={"IncidentId": "CONFIG_CRITICAL_FUNCTIONS"})
        item = response.get("Item", {})
        current_functions = item.get("functions", [])
        
        if action == "add" and function_name:
            if function_name not in current_functions:
                current_functions.append(function_name)
        elif action == "remove" and function_name:
            if function_name in current_functions:
                current_functions.remove(function_name)
        elif functions is not None:
            # Replace entire list
            current_functions = functions
        
        # Save back
        table.put_item(Item={
            "IncidentId": "CONFIG_CRITICAL_FUNCTIONS",
            "functions": current_functions,
            "CreatedAt": datetime.utcnow().isoformat() + "Z"
        })
        
        return {
            "success": True,
            "criticalFunctions": current_functions,
            "message": f"Critical functions updated. Total: {len(current_functions)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_auto_remediation_config():
    """Get auto-remediation configuration for each scenario type"""
    try:
        response = table.get_item(Key={"IncidentId": "CONFIG_AUTO_REMEDIATION"})
        item = response.get("Item", {})
        
        # Default config - scenarios that auto-remediate by default
        default_config = {
            "lambdaTimeout": True,
            "outOfMemory": True,
            "throttling": False,
            "connectionPool": False,
            "cacheCorruption": False,
            "healthCheck": False,
            "diskFull": False,
            "authFailure": False,
            "dependencyTimeout": False,
            "dlqEscalation": False
        }
        
        # Merge saved config with defaults
        saved_config = item.get("scenarios", {})
        merged_config = {**default_config, **saved_config}
        
        return {
            "success": True,
            "config": merged_config,
            "lastUpdated": item.get("CreatedAt", None)
        }
    except Exception as e:
        print(f"[ERROR] Failed to get auto-remediation config: {str(e)}")
        return {
            "success": True,
            "config": {
                "lambdaTimeout": True,
                "outOfMemory": True,
                "throttling": False,
                "connectionPool": False,
                "cacheCorruption": False,
                "healthCheck": False,
                "diskFull": False,
                "authFailure": False,
                "dependencyTimeout": False,
                "dlqEscalation": False
            },
            "lastUpdated": None
        }


def update_auto_remediation_config(body):
    """Update auto-remediation configuration"""
    config = body.get("config", {})
    
    try:
        # Save config to DynamoDB
        table.put_item(Item={
            "IncidentId": "CONFIG_AUTO_REMEDIATION",
            "scenarios": config,
            "CreatedAt": datetime.utcnow().isoformat() + "Z"
        })
        
        return {
            "success": True,
            "config": config,
            "message": "Auto-remediation configuration updated successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_error_frequency_count(error_signature, log_group):
    """Get count of similar errors in last 24 hours"""
    if not error_signature:
        return 1
    
    try:
        from datetime import timedelta
        from boto3.dynamodb.conditions import Attr
        
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_24h_str = last_24h.isoformat() + "Z"
        
        response = table.scan(
            FilterExpression=Attr('ErrorSignature').eq(error_signature) & 
                           Attr('CreatedAt').gt(last_24h_str) &
                           Attr('LogGroup').eq(log_group)
        )
        
        return len(response.get('Items', []))
    except Exception as e:
        print(f"[ERROR] Failed to get error frequency: {str(e)}")
        return 1


def get_error_occurrences(error_signature, log_group):
    """Get list of related incidents - by error signature or same log group"""
    try:
        from datetime import timedelta
        from boto3.dynamodb.conditions import Attr
        
        now = datetime.utcnow()
        # Extended to 7 days for better related incident discovery
        last_week = now - timedelta(days=7)
        last_week_str = last_week.isoformat() + "Z"
        
        items = []
        
        # First try to find incidents with same error signature (if available)
        if error_signature:
            response = table.scan(
                FilterExpression=Attr('ErrorSignature').eq(error_signature) & 
                               Attr('CreatedAt').gt(last_week_str)
            )
            items = response.get('Items', [])
        
        # If no matches by signature, find incidents from same log group
        if not items and log_group:
            response = table.scan(
                FilterExpression=Attr('LogGroup').eq(log_group) & 
                               Attr('CreatedAt').gt(last_week_str)
            )
            items = response.get('Items', [])
        
        occurrences = []
        for item in items:
            occurrences.append({
                'timestamp': item.get('CreatedAt'),
                'incidentId': item.get('IncidentId'),
                'ticketNumber': item.get('TicketNumber'),
                'status': item.get('Status', 'UNKNOWN'),
                'summary': item.get('AnalysisResult', {}).get('summary', 'N/A')[:100]
            })
        
        # Sort by timestamp descending
        occurrences.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return occurrences[:10]  # Return last 10 occurrences
    except Exception as e:
        print(f"[ERROR] Failed to get error occurrences: {str(e)}")
        return []


def resolve_incident(incident_id, resolved_by):
    """Mark an incident as resolved"""
    try:
        # Get the incident
        response = table.get_item(Key={"IncidentId": incident_id})
        item = response.get("Item")
        
        if not item:
            return {"success": False, "error": "Incident not found"}
        
        # Update status
        table.update_item(
            Key={"IncidentId": incident_id},
            UpdateExpression="SET #status = :status, ResolvedAt = :resolvedAt, ResolvedBy = :resolvedBy",
            ExpressionAttributeNames={
                "#status": "Status"
            },
            ExpressionAttributeValues={
                ":status": "RESOLVED",
                ":resolvedAt": datetime.utcnow().isoformat() + "Z",
                ":resolvedBy": resolved_by
            }
        )

        # Notify resolution
        item["Status"] = "RESOLVED"
        item["ResolvedAt"] = datetime.utcnow().isoformat() + "Z"
        item["ResolvedBy"] = resolved_by
        publish_stage_notification(
            stage="Resolved",
            item=item,
            status="RESOLVED",
            details=f"Incident resolved by {resolved_by}",
        )
        
        return {
            "success": True,
            "incidentId": incident_id,
            "status": "RESOLVED",
            "message": f"Incident {incident_id} marked as resolved by {resolved_by}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
