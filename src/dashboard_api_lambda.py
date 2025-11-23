import json
import os
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME", "RCRARootCauseTable")
table = dynamodb.Table(table_name)


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal to JSON"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def cors_headers():
    """Return CORS headers for API responses"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
    }


def handler(event, context):
    """
    API Gateway Lambda handler for RCRA Dashboard
    Routes:
    - GET /incidents - List all incidents with pagination
    - GET /incidents/{id} - Get specific incident details
    - GET /statistics - Get system statistics
    """

    http_method = event.get("httpMethod", "")
    path = event.get("path", "")
    path_parameters = event.get("pathParameters") or {}
    query_parameters = event.get("queryStringParameters") or {}

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
            response_data = get_incident_by_id(path_parameters["id"])
        elif path == "/statistics" or path.endswith("/statistics"):
            response_data = get_statistics()
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

    # Sort by CreatedAt descending
    items.sort(key=lambda x: x.get("CreatedAt", ""), reverse=True)

    # Parse and flatten data for easier frontend consumption
    incidents = []
    for item in items:
        analysis = item.get("AnalysisResult", {})
        incident = {
            "incidentId": item.get("IncidentId"),
            "timestamp": item.get("CreatedAt"),
            "logGroup": item.get("LogGroup"),
            "logStream": item.get("LogStream"),
            "rawMessage": item.get("RawLogMessage", "")[:200],  # Truncate for list view
            "summary": analysis.get("summary", "N/A"),
            "severity": analysis.get("severity", "UNKNOWN"),
            "rootCause": analysis.get("probable_root_cause", "N/A"),
            "tags": analysis.get("tags", []),
            "remediationEligible": item.get("RemediationResult", {}).get(
                "autoRemediationEligible", False
            ),
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

    incident_detail = {
        "incidentId": item.get("IncidentId"),
        "timestamp": item.get("CreatedAt"),
        "logGroup": item.get("LogGroup"),
        "logStream": item.get("LogStream"),
        "rawMessage": item.get("RawLogMessage", ""),
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
        },
    }

    return incident_detail


def get_statistics():
    """Calculate and return system statistics"""
    # Scan all items (in production, consider using DynamoDB Streams or separate stats table)
    response = table.scan()
    items = response.get("Items", [])

    # Calculate statistics
    total_incidents = len(items)
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
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
        recent_incidents.append(
            {
                "incidentId": item.get("IncidentId"),
                "timestamp": item.get("CreatedAt"),
                "summary": analysis.get("summary", "N/A"),
                "severity": analysis.get("severity", "UNKNOWN"),
            }
        )

    statistics = {
        "overview": {
            "totalIncidents": total_incidents,
            "incidents24h": incidents_24h,
            "remediationEligible": remediation_eligible,
            "avgSeverity": _calculate_avg_severity(severity_counts, total_incidents),
        },
        "severityBreakdown": severity_counts,
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

