"""
Dummy Application Lambda - Simulates various production errors
for testing RCRA auto-remediation capabilities
"""

import json
import random
import time
import os
from datetime import datetime


def handler(event, context):
    """
    Simulates different types of errors that can be auto-remediated.
    Query parameter 'scenario' determines which error to generate.
    """
    
    scenario = event.get('queryStringParameters', {}).get('scenario', 'random') if event.get('queryStringParameters') else 'random'
    
    if scenario == 'random':
        scenario = random.choice([
            'timeout', 'memory', 'connection', 'api_throttle', 
            'cache_error', 'health_check', 'dlq', 'success'
        ])
    
    print(f"[DUMMY_APP] Executing scenario: {scenario}")
    
    try:
        if scenario == 'timeout':
            return simulate_timeout()
        elif scenario == 'memory':
            return simulate_memory_error()
        elif scenario == 'connection':
            return simulate_connection_error()
        elif scenario == 'api_throttle':
            return simulate_api_throttle()
        elif scenario == 'cache_error':
            return simulate_cache_error()
        elif scenario == 'health_check':
            return simulate_health_check_failure()
        elif scenario == 'dlq':
            return simulate_dlq_message()
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'message': 'Application running normally',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise


def simulate_timeout():
    """Simulates Lambda timeout - takes too long to execute"""
    print("ERROR: Lambda execution timeout imminent")
    print(f"Current timeout: {os.environ.get('AWS_LAMBDA_FUNCTION_TIMEOUT', 'unknown')} seconds")
    print("Recommendation: Increase Lambda timeout configuration")
    
    # Simulate long-running operation
    time.sleep(2)
    
    raise Exception(
        "ERROR: Lambda timeout - Operation took too long to complete. "
        "Current timeout setting is insufficient for this workload. "
        "Auto-remediation: Increase Lambda timeout from 30s to 60s"
    )


def simulate_memory_error():
    """Simulates out-of-memory error"""
    print("ERROR: Lambda running out of memory")
    print(f"Current memory: {os.environ.get('AWS_LAMBDA_MEMORY_SIZE', 'unknown')} MB")
    print("Memory usage approaching limit")
    
    # Simulate memory pressure
    data = []
    for i in range(1000):
        data.append([0] * 10000)
    
    raise Exception(
        "ERROR: OutOfMemoryError - Lambda function memory limit exceeded. "
        "Current allocation: 512MB, Peak usage: 510MB. "
        "Auto-remediation: Increase memory allocation to 1024MB"
    )


def simulate_connection_error():
    """Simulates database/external service connection failure"""
    print("ERROR: Database connection pool exhausted")
    print("Active connections: 50/50 (max reached)")
    print("Connection timeout: 30 seconds exceeded")
    
    raise Exception(
        "ERROR: ConnectionPoolExhausted - Unable to acquire database connection. "
        "All connections in pool are busy or timed out. "
        "Auto-remediation: Restart Lambda to reset connection pool"
    )


def simulate_api_throttle():
    """Simulates API Gateway throttling"""
    print("ERROR: API Gateway throttling detected")
    print("Current rate: 10,000 requests/second (limit reached)")
    print("Throttled requests: 1,500 in last minute")
    
    raise Exception(
        "ERROR: TooManyRequestsException - API Gateway throttle limit exceeded. "
        "Current limit: 10,000 req/s, Actual rate: 12,500 req/s. "
        "Auto-remediation: Request quota increase or enable caching"
    )


def simulate_cache_error():
    """Simulates cache corruption/invalidation issues"""
    print("ERROR: Cache corruption detected")
    print("Redis cache keys returning invalid data")
    print("Cache hit rate dropped from 95% to 12%")
    
    raise Exception(
        "ERROR: CacheCorruptionException - Cache entries contain invalid data. "
        "Multiple cache misses and stale data detected. "
        "Auto-remediation: Flush cache and trigger rebuild"
    )


def simulate_health_check_failure():
    """Simulates failed health check"""
    print("ERROR: Health check endpoint failing")
    print("Last successful health check: 5 minutes ago")
    print("Service appears unresponsive")
    
    raise Exception(
        "ERROR: HealthCheckFailed - Service health endpoint not responding. "
        "Status: UNHEALTHY, Last success: 5m ago. "
        "Auto-remediation: Restart service/Lambda"
    )


def simulate_dlq_message():
    """Simulates message processing failure that goes to DLQ"""
    print("ERROR: Message processing failed")
    print("Message has been retried 3 times")
    print("Moving to Dead Letter Queue")
    
    raise Exception(
        "ERROR: MessageProcessingFailed - Unable to process SQS message. "
        "Retry count: 3/3, Moving to DLQ. "
        "Auto-remediation: Analyze and replay DLQ messages"
    )

