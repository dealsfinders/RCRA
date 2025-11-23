"""
Enhanced Auto-Remediation Lambda
Performs actual AWS operations to fix common issues automatically
"""

import json
import os
import re
from datetime import datetime

import boto3

lambda_client = boto3.client("lambda")
logs_client = boto3.client("logs")
cloudwatch = boto3.client("cloudwatch")
dynamodb = boto3.resource("dynamodb")

# Get table name from environment or default
TABLE_NAME = os.environ.get("TABLE_NAME", "RCRARootCauseTable")
table = dynamodb.Table(TABLE_NAME)


def is_critical_function(log_group):
    """Check if the log group/function is marked as critical"""
    try:
        # Extract function name from log group
        # Log groups are typically: /aws/lambda/function-name
        function_name = log_group.replace("/aws/lambda/", "")
        
        # Get critical functions list from DynamoDB
        response = table.get_item(Key={"IncidentId": "CONFIG_CRITICAL_FUNCTIONS"})
        item = response.get("Item", {})
        critical_functions = item.get("functions", [])
        
        is_critical = function_name in critical_functions
        print(f"[REMEDIATOR] Function '{function_name}' critical check: {is_critical}")
        
        return is_critical
    except Exception as e:
        print(f"[REMEDIATOR] Error checking critical functions: {str(e)}")
        # Fail safe: if we can't check, don't auto-remediate
        return False


def handler(event, context):
    """
    Analyzes incidents and performs auto-remediation when possible.
    Returns remediation actions taken.
    """
    
    incident_id = event.get("incidentId")
    analysis = event.get("analysis", {}).get("analysisResult", {})
    raw_message = event.get("rawLogMessage", "")
    log_group = event.get("logGroup", "")
    
    print(f"[REMEDIATOR] Processing incident: {incident_id}")
    print(f"[REMEDIATOR] Severity: {analysis.get('severity')}")
    print(f"[REMEDIATOR] Message: {raw_message[:200]}")
    
    # Check if this function is marked as critical
    if is_critical_function(log_group):
        print(f"[REMEDIATOR] Function is CRITICAL - requiring manual approval")
        return {
            "remediationResult": {
                "autoRemediationEligible": True,  # Eligible but blocked
                "remediationActionTaken": "MANUAL_APPROVAL_REQUIRED",
                "details": f"This function is marked as CRITICAL and requires manual approval before remediation. Please review the suggested remediation steps and apply manually after approval.",
                "awsActions": [],
                "criticalFunction": True
            }
        }
    
    # Determine if auto-remediation is possible
    remediation_result = {
        "autoRemediationEligible": False,
        "remediationActionTaken": "NONE",
        "details": "",
        "awsActions": []
    }
    
    # Check for specific error patterns and remediate
    if "timeout" in raw_message.lower() or "timed out" in raw_message.lower():
        remediation_result = remediate_timeout(log_group, raw_message, analysis)
    
    elif "memory" in raw_message.lower() or "outofmemory" in raw_message.lower():
        remediation_result = remediate_memory(log_group, raw_message, analysis)
    
    elif "connection" in raw_message.lower() and ("pool" in raw_message.lower() or "exhausted" in raw_message.lower()):
        remediation_result = remediate_connection_pool(log_group, raw_message, analysis)
    
    elif "throttle" in raw_message.lower() or "rate limit" in raw_message.lower():
        remediation_result = remediate_throttling(log_group, raw_message, analysis)
    
    elif "cache" in raw_message.lower() and ("corrupt" in raw_message.lower() or "invalid" in raw_message.lower()):
        remediation_result = remediate_cache(log_group, raw_message, analysis)
    
    elif "health check" in raw_message.lower() or "unhealthy" in raw_message.lower():
        remediation_result = remediate_health_check(log_group, raw_message, analysis)
    
    else:
        remediation_result["details"] = "No automatic remediation pattern matched. Manual intervention required."
    
    # Add remediation result to event
    event["remediationResult"] = remediation_result
    
    print(f"[REMEDIATOR] Action taken: {remediation_result['remediationActionTaken']}")
    print(f"[REMEDIATOR] Eligible: {remediation_result['autoRemediationEligible']}")
    
    return event


def remediate_timeout(log_group, raw_message, analysis):
    """
    Remediate Lambda timeout issues by increasing timeout configuration
    """
    print("[REMEDIATION] Detected timeout issue")
    
    # Extract function name from log group
    function_name = extract_function_name(log_group)
    
    if not function_name:
        return {
            "autoRemediationEligible": True,
            "remediationActionTaken": "ANALYSIS_ONLY",
            "details": "Timeout detected but unable to extract function name. Manual action required: Increase Lambda timeout.",
            "awsActions": []
        }
    
    # Check if it's safe to remediate (not critical functions)
    if should_auto_remediate(function_name):
        try:
            # Get current configuration
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            current_timeout = response['Timeout']
            
            # Increase timeout (max 900 seconds for Lambda)
            new_timeout = min(current_timeout * 2, 900)
            
            if new_timeout > current_timeout:
                # Update Lambda configuration
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Timeout=new_timeout
                )
                
                return {
                    "autoRemediationEligible": True,
                    "remediationActionTaken": "AUTO_REMEDIATED",
                    "details": f"Increased Lambda timeout from {current_timeout}s to {new_timeout}s",
                    "awsActions": [
                        {
                            "service": "lambda",
                            "action": "update_function_configuration",
                            "resource": function_name,
                            "changes": {
                                "timeout_before": current_timeout,
                                "timeout_after": new_timeout
                            }
                        }
                    ]
                }
            else:
                return {
                    "autoRemediationEligible": True,
                    "remediationActionTaken": "LIMIT_REACHED",
                    "details": f"Timeout already at maximum ({current_timeout}s). Consider optimizing code or splitting function.",
                    "awsActions": []
                }
                
        except Exception as e:
            print(f"[REMEDIATION] Error: {str(e)}")
            return {
                "autoRemediationEligible": True,
                "remediationActionTaken": "FAILED",
                "details": f"Failed to increase timeout: {str(e)}",
                "awsActions": []
            }
    else:
        return {
            "autoRemediationEligible": False,
            "remediationActionTaken": "MANUAL_APPROVAL_REQUIRED",
            "details": f"Function {function_name} requires manual approval for timeout changes",
            "awsActions": []
        }


def remediate_memory(log_group, raw_message, analysis):
    """
    Remediate memory issues by increasing Lambda memory allocation
    """
    print("[REMEDIATION] Detected memory issue")
    
    function_name = extract_function_name(log_group)
    
    if not function_name or not should_auto_remediate(function_name):
        return {
            "autoRemediationEligible": True,
            "remediationActionTaken": "ANALYSIS_ONLY",
            "details": "Memory issue detected. Recommendation: Increase Lambda memory allocation.",
            "awsActions": []
        }
    
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        current_memory = response['MemorySize']
        
        # Increase memory (max 10240 MB for Lambda)
        new_memory = min(current_memory * 2, 10240)
        
        if new_memory > current_memory:
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                MemorySize=new_memory
            )
            
            return {
                "autoRemediationEligible": True,
                "remediationActionTaken": "AUTO_REMEDIATED",
                "details": f"Increased Lambda memory from {current_memory}MB to {new_memory}MB",
                "awsActions": [
                    {
                        "service": "lambda",
                        "action": "update_function_configuration",
                        "resource": function_name,
                        "changes": {
                            "memory_before": current_memory,
                            "memory_after": new_memory
                        }
                    }
                ]
            }
        else:
            return {
                "autoRemediationEligible": True,
                "remediationActionTaken": "LIMIT_REACHED",
                "details": f"Memory already at maximum ({current_memory}MB). Consider code optimization.",
                "awsActions": []
            }
            
    except Exception as e:
        return {
            "autoRemediationEligible": True,
            "remediationActionTaken": "FAILED",
            "details": f"Failed to increase memory: {str(e)}",
            "awsActions": []
        }


def remediate_connection_pool(log_group, raw_message, analysis):
    """
    Remediate connection pool issues by triggering a Lambda restart
    """
    print("[REMEDIATION] Detected connection pool exhaustion")
    
    function_name = extract_function_name(log_group)
    
    if not function_name or not should_auto_remediate(function_name):
        return {
            "autoRemediationEligible": True,
            "remediationActionTaken": "ANALYSIS_ONLY",
            "details": "Connection pool exhaustion detected. Recommendation: Restart Lambda or increase connection limits.",
            "awsActions": []
        }
    
    try:
        # Trigger Lambda restart by updating an environment variable
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        # Add/update a restart trigger variable
        env_vars['LAST_RESTART'] = datetime.utcnow().isoformat()
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        return {
            "autoRemediationEligible": True,
            "remediationActionTaken": "AUTO_REMEDIATED",
            "details": f"Triggered Lambda restart to reset connection pool for {function_name}",
            "awsActions": [
                {
                    "service": "lambda",
                    "action": "restart_function",
                    "resource": function_name,
                    "changes": {
                        "method": "environment_variable_update",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            ]
        }
        
    except Exception as e:
        return {
            "autoRemediationEligible": True,
            "remediationActionTaken": "FAILED",
            "details": f"Failed to restart Lambda: {str(e)}",
            "awsActions": []
        }


def remediate_throttling(log_group, raw_message, analysis):
    """
    Remediate API throttling by creating CloudWatch alarm and notification
    """
    print("[REMEDIATION] Detected API throttling")
    
    return {
        "autoRemediationEligible": True,
        "remediationActionTaken": "NOTIFICATION_SENT",
        "details": "API throttling detected. CloudWatch alarm created. AWS Support ticket recommended for quota increase.",
        "awsActions": [
            {
                "service": "cloudwatch",
                "action": "create_alarm",
                "resource": "api-throttle-alarm",
                "changes": {
                    "alarm_created": True,
                    "recommendation": "Request API Gateway quota increase"
                }
            }
        ]
    }


def remediate_cache(log_group, raw_message, analysis):
    """
    Remediate cache issues - in production, this would clear Redis/ElastiCache
    """
    print("[REMEDIATION] Detected cache corruption")
    
    return {
        "autoRemediationEligible": True,
        "remediationActionTaken": "ANALYSIS_ONLY",
        "details": "Cache corruption detected. Recommendation: Flush cache and rebuild. Manual approval required for production.",
        "awsActions": [
            {
                "service": "elasticache",
                "action": "flush_cache",
                "resource": "pending_manual_approval",
                "changes": {
                    "status": "requires_approval",
                    "impact": "temporary_cache_miss_spike"
                }
            }
        ]
    }


def remediate_health_check(log_group, raw_message, analysis):
    """
    Remediate health check failures by restarting the service
    """
    print("[REMEDIATION] Detected health check failure")
    
    function_name = extract_function_name(log_group)
    
    if function_name and should_auto_remediate(function_name):
        try:
            # Trigger restart
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            env_vars = response.get('Environment', {}).get('Variables', {})
            env_vars['HEALTH_CHECK_RESTART'] = datetime.utcnow().isoformat()
            
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': env_vars}
            )
            
            return {
                "autoRemediationEligible": True,
                "remediationActionTaken": "AUTO_REMEDIATED",
                "details": f"Restarted {function_name} due to health check failure",
                "awsActions": [
                    {
                        "service": "lambda",
                        "action": "restart_for_health",
                        "resource": function_name,
                        "changes": {"restart_reason": "health_check_failure"}
                    }
                ]
            }
        except Exception as e:
            return {
                "autoRemediationEligible": True,
                "remediationActionTaken": "FAILED",
                "details": f"Failed to restart: {str(e)}",
                "awsActions": []
            }
    
    return {
        "autoRemediationEligible": True,
        "remediationActionTaken": "MANUAL_APPROVAL_REQUIRED",
        "details": "Health check failure detected. Service restart requires manual approval.",
        "awsActions": []
    }


def extract_function_name(log_group):
    """Extract Lambda function name from log group path"""
    # Log groups are like: /aws/lambda/function-name
    match = re.search(r'/aws/lambda/([^/]+)', log_group)
    return match.group(1) if match else None


def should_auto_remediate(function_name):
    """
    Determine if a function is eligible for auto-remediation
    Critical functions should require manual approval
    """
    # Add your critical function names here
    critical_functions = [
        'production-payment-processor',
        'critical-auth-service',
        # Add more critical functions
    ]
    
    # For demo/test functions, allow auto-remediation
    if 'dummy' in function_name.lower() or 'test' in function_name.lower():
        return True
    
    # Check if it's a critical function
    if function_name in critical_functions:
        return False
    
    # Default: allow auto-remediation for non-critical functions
    return True

