"""
Health check Lambda function for FX Analysis System
Non-VPC configuration for direct access to AWS services
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

def lambda_handler(event, context):
    """
    Health check endpoint - returns system status and metrics
    Non-VPC Lambda with direct access to CloudWatch, S3, etc.
    """
    
    logs_client = boto3.client('logs')
    s3_client = boto3.client('s3')
    scheduler_client = boto3.client('scheduler')
    cloudwatch = boto3.client('cloudwatch')
    
    # Environment variables
    log_group = os.environ.get('LOG_GROUP_NAME', '/ecs/analyze-fx')
    s3_bucket = os.environ.get('S3_BUCKET', 'analyze-fx-455931011903-apne1')
    
    try:
        # 1. Get last successful execution
        last_success_data = get_last_success(logs_client, log_group)
        
        # 2. Calculate error counts (last 24h)
        error_counts = get_error_counts(logs_client, log_group)
        
        # 3. Calculate metrics (7 days)
        metrics = calculate_metrics(logs_client, log_group)
        
        # 4. Get next scheduled run
        next_run = get_next_scheduled_run(scheduler_client)
        
        # 5. Put metrics to CloudWatch
        put_health_metrics(cloudwatch, metrics)
        
        # 6. Check system health
        health_status = determine_health_status(
            last_success_data,
            error_counts,
            metrics
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': health_status,
                'last_success_ts': last_success_data.get('timestamp'),
                'last_run_id': last_success_data.get('run_id'),
                'error_counts': error_counts,
                'next_scheduled_run': next_run,
                'system_metrics': metrics
            })
        }
        
    except Exception as e:
        print(f"Error in health check: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }


def get_last_success(logs_client, log_group: str) -> Dict:
    """
    Get last successful execution using CloudWatch Logs Insights
    修正2: 実際のstart_query/get_query_results実装
    """
    
    # Start query - include no-trade as successful execution
    query_string = """
    fields @timestamp, @message
    | filter @message like /status.*(?:success|no-trade)/
    | parse @message /"run_id":"(?<run_id>[^"]+)"/
    | sort @timestamp desc
    | limit 1
    """
    
    response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int((datetime.utcnow() - timedelta(days=7)).timestamp()),
        endTime=int(datetime.utcnow().timestamp()),
        queryString=query_string
    )
    
    query_id = response['queryId']
    
    # Wait for query completion
    results = wait_for_query_results(logs_client, query_id)
    
    if results:
        # Parse the first result
        for field in results[0]:
            if field['field'] == '@timestamp':
                timestamp = field['value']
            elif field['field'] == 'run_id':
                run_id = field['value']
        
        return {
            'timestamp': timestamp,
            'run_id': run_id if 'run_id' in locals() else 'unknown'
        }
    
    return {
        'timestamp': 'No successful runs in last 7 days',
        'run_id': 'N/A'
    }


def get_error_counts(logs_client, log_group: str) -> Dict[str, int]:
    """
    Get error counts by module (last 24 hours)
    """
    
    query_string = """
    fields @message
    | filter @message like /ERROR/
    | parse @message /\\[(?<module>[^\\]]+)\\].*ERROR/
    | stats count() by module
    """
    
    response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int((datetime.utcnow() - timedelta(hours=24)).timestamp()),
        endTime=int(datetime.utcnow().timestamp()),
        queryString=query_string
    )
    
    query_id = response['queryId']
    results = wait_for_query_results(logs_client, query_id)
    
    error_counts = {}
    for result in results:
        module = None
        count = None
        for field in result:
            if field['field'] == 'module':
                module = field['value']
            elif field['field'] == 'count()':
                count = int(field['value'])
        
        if module and count:
            error_counts[module] = count
    
    return error_counts


def calculate_metrics(logs_client, log_group: str) -> Dict:
    """
    Calculate system metrics (7 days)
    """
    
    # Query for execution times and success rates - include no-trade as successful
    query_string = """
    fields @timestamp, @message
    | filter @message like /Analysis run completed/
    | parse @message /status=(?<status>[^,]+)/
    | parse @message /execution_time_ms=(?<exec_ms>\\d+)/
    | stats 
        count() as total_runs,
        count(status = "success" or status = "no-trade") as successful_runs,
        avg(exec_ms) as avg_execution_ms
    """
    
    response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int((datetime.utcnow() - timedelta(days=7)).timestamp()),
        endTime=int(datetime.utcnow().timestamp()),
        queryString=query_string
    )
    
    query_id = response['queryId']
    results = wait_for_query_results(logs_client, query_id)
    
    if results and len(results) > 0:
        result = results[0]
        total_runs = 0
        successful_runs = 0
        avg_execution_ms = 0
        
        for field in result:
            if field['field'] == 'total_runs':
                total_runs = int(field['value'])
            elif field['field'] == 'successful_runs':
                successful_runs = int(field['value'])
            elif field['field'] == 'avg_execution_ms':
                avg_execution_ms = float(field['value'])
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        # Today's runs
        today_query = """
        fields @timestamp
        | filter @message like /Analysis run/
        | stats count() as today_runs
        """
        
        today_response = logs_client.start_query(
            logGroupName=log_group,
            startTime=int((datetime.utcnow().replace(hour=0, minute=0, second=0)).timestamp()),
            endTime=int(datetime.utcnow().timestamp()),
            queryString=today_query
        )
        
        today_results = wait_for_query_results(logs_client, today_response['queryId'])
        today_runs = 0
        
        if today_results and len(today_results) > 0:
            for field in today_results[0]:
                if field['field'] == 'today_runs':
                    today_runs = int(field['value'])
        
        return {
            'avg_execution_time_ms': round(avg_execution_ms, 2),
            'success_rate_7d': round(success_rate, 2),
            'total_runs_7d': total_runs,
            'successful_runs_7d': successful_runs,
            'total_runs_today': today_runs
        }
    
    return {
        'avg_execution_time_ms': 0,
        'success_rate_7d': 0,
        'total_runs_7d': 0,
        'successful_runs_7d': 0,
        'total_runs_today': 0
    }


def wait_for_query_results(logs_client, query_id: str, max_wait: int = 30) -> List:
    """
    Poll for query results until complete
    """
    
    for _ in range(max_wait):
        response = logs_client.get_query_results(queryId=query_id)
        status = response['status']
        
        if status == 'Complete':
            return response['results']
        elif status in ['Failed', 'Cancelled']:
            raise Exception(f"Query {query_id} failed with status: {status}")
        
        time.sleep(1)
    
    raise Exception(f"Query {query_id} timed out after {max_wait} seconds")


def get_next_scheduled_run(scheduler_client) -> str:
    """
    Get next scheduled run time
    """
    
    try:
        # Get main analysis scheduler
        response = scheduler_client.get_schedule(
            Name='analyze-fx-prod-0800-jst'
        )
        
        # Parse schedule expression and timezone
        schedule_expr = response.get('ScheduleExpression', '')
        timezone = response.get('ScheduleExpressionTimezone', 'UTC')
        
        # For now, return the raw expression
        # In production, calculate actual next run time
        return f"Next run: {schedule_expr} ({timezone})"
        
    except Exception as e:
        return f"Unable to determine next run: {str(e)}"


def put_health_metrics(cloudwatch, metrics: Dict):
    """
    Put custom metrics to CloudWatch
    """
    
    try:
        cloudwatch.put_metric_data(
            Namespace='FX/Health',
            MetricData=[
                {
                    'MetricName': 'SuccessRate7d',
                    'Value': metrics['success_rate_7d'],
                    'Unit': 'Percent',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'AvgExecutionTime',
                    'Value': metrics['avg_execution_time_ms'],
                    'Unit': 'Milliseconds',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'TotalRunsToday',
                    'Value': metrics['total_runs_today'],
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    except Exception as e:
        print(f"Failed to put metrics: {str(e)}")


def determine_health_status(last_success: Dict, errors: Dict, metrics: Dict) -> str:
    """
    Determine overall system health
    """
    
    # Check if last success was recent (within 24 hours)
    if last_success.get('timestamp') and last_success['timestamp'] != 'No successful runs in last 7 days':
        # Parse timestamp and check recency
        # For now, assume healthy if we have a recent success
        pass
    
    # Check error threshold
    total_errors = sum(errors.values())
    
    # Check success rate
    success_rate = metrics.get('success_rate_7d', 0)
    
    if success_rate >= 90 and total_errors < 10:
        return 'healthy'
    elif success_rate >= 70 and total_errors < 50:
        return 'degraded'
    else:
        return 'unhealthy'