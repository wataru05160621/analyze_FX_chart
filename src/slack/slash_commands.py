"""
Slack slash command handlers with proper signature verification
Using Bolt for Python with API Gateway + Lambda
"""

import json
import os
import boto3
import requests
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from datetime import datetime

# Initialize Slack app with proper credentials
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=True
)

# Environment variables
HEALTH_API_URL = os.environ.get("HEALTH_API_URL", "https://api-gateway-url/prod/health")
ECS_CLUSTER = "analyze-fx-cluster"
ECS_TASK_DEF = "analyze-fx"

# AWS clients
ecs_client = boto3.client('ecs')
scheduler_client = boto3.client('scheduler')


@app.command("/fx")
def handle_fx_command(ack, command, client):
    """
    Handle /fx slash command with subcommands
    修正4: 署名検証はBoltが自動的に処理
    """
    ack()  # Acknowledge command receipt
    
    # Parse subcommand
    text = command.get('text', '').strip()
    parts = text.split()
    subcommand = parts[0] if parts else 'help'
    
    if subcommand == 'status':
        handle_status_command(command, client)
    elif subcommand == 'run':
        handle_run_command(command, client, parts[1:])
    elif subcommand == 'help':
        handle_help_command(command, client)
    else:
        client.chat_postMessage(
            channel=command['channel_id'],
            text=f"Unknown subcommand: {subcommand}. Use `/fx help` for available commands."
        )


def handle_status_command(command, client):
    """
    Handle /fx status - show system health
    """
    try:
        # Call health API
        response = requests.get(HEALTH_API_URL, timeout=10)
        health_data = response.json()
        
        # Determine status emoji
        status_emoji = {
            'healthy': '🟢',
            'degraded': '🟡',
            'unhealthy': '🔴',
            'error': '⚫'
        }.get(health_data.get('status', 'error'), '⚫')
        
        # Build response blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🏥 FX Analysis System Status"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:* {status_emoji} {health_data.get('status', 'unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Last Success:* {format_timestamp(health_data.get('last_success_ts'))}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Run ID:* `{health_data.get('last_run_id', 'N/A')}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Next Run:* {health_data.get('next_scheduled_run', 'Unknown')}"
                    }
                ]
            }
        ]
        
        # Add metrics if available
        if 'system_metrics' in health_data:
            metrics = health_data['system_metrics']
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 System Metrics (7 days)*"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Success Rate:* {metrics.get('success_rate_7d', 0):.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Avg Execution:* {metrics.get('avg_execution_time_ms', 0):.0f}ms"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Runs:* {metrics.get('total_runs_7d', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Today's Runs:* {metrics.get('total_runs_today', 0)}"
                    }
                ]
            })
        
        # Add error counts if any
        if health_data.get('error_counts'):
            error_text = "*⚠️ Recent Errors (24h)*\n"
            for module, count in health_data['error_counts'].items():
                error_text += f"• {module}: {count}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": error_text
                }
            })
        
        # Send response
        client.chat_postMessage(
            channel=command['channel_id'],
            blocks=blocks,
            text="System status retrieved successfully"
        )
        
    except Exception as e:
        client.chat_postMessage(
            channel=command['channel_id'],
            text=f"❌ Failed to retrieve system status: {str(e)}"
        )


def handle_run_command(command, client, args):
    """
    Handle /fx run [mode] - trigger manual analysis run
    """
    mode = args[0] if args else 'dryrun'
    
    if mode not in ['dryrun', 'production']:
        client.chat_postMessage(
            channel=command['channel_id'],
            text="Invalid mode. Use `/fx run dryrun` or `/fx run production`"
        )
        return
    
    try:
        # Run ECS task
        response = ecs_client.run_task(
            cluster=ECS_CLUSTER,
            taskDefinition=ECS_TASK_DEF,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [
                        'subnet-06fba36a849bb6647',
                        'subnet-02aef8bf85b9ceb0d'
                    ],
                    'securityGroups': ['sg-03cb601e40f6e32ac'],
                    'assignPublicIp': 'ENABLED'
                }
            },
            overrides={
                'containerOverrides': [{
                    'name': 'analyze-fx',
                    'environment': [
                        {'name': 'RUN_MODE', 'value': mode},
                        {'name': 'TRIGGERED_BY', 'value': f"slack:{command['user_id']}"},
                        {'name': 'SLACK_RESPONSE_URL', 'value': command['response_url']}
                    ]
                }]
            }
        )
        
        # Extract task ID
        task_arn = response['tasks'][0]['taskArn']
        task_id = task_arn.split('/')[-1]
        
        # Send immediate response
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ Analysis task started in *{mode}* mode"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Task ID:* `{task_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Triggered by:* <@{command['user_id']}>"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')}"
                    }
                ]
            }
        ]
        
        if mode == 'dryrun':
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "ℹ️ *Dry-run mode:* Notion pages will be tagged as TEST, Slack notifications to #fx-test"
                }
            })
        
        client.chat_postMessage(
            channel=command['channel_id'],
            blocks=blocks,
            text=f"Analysis started in {mode} mode"
        )
        
    except Exception as e:
        client.chat_postMessage(
            channel=command['channel_id'],
            text=f"❌ Failed to start analysis: {str(e)}"
        )


def handle_help_command(command, client):
    """
    Handle /fx help - show available commands
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📖 FX Analysis Commands"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Available commands:*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "• `/fx status` - Show system health and metrics\n"
                        "• `/fx run [mode]` - Run analysis (dryrun or production)\n"
                        "• `/fx help` - Show this help message"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 *Tip:* Use `/fx run dryrun` to test without affecting production"
                }
            ]
        }
    ]
    
    client.chat_postMessage(
        channel=command['channel_id'],
        blocks=blocks,
        text="FX Analysis command help"
    )


def format_timestamp(ts):
    """Format timestamp for display"""
    if not ts or ts == 'No successful runs in last 7 days':
        return ts
    
    try:
        # Parse and format the timestamp
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M JST')
    except:
        return ts


# Lambda handler for API Gateway integration
def lambda_handler(event, context):
    """
    Lambda handler with Slack Bolt adapter
    修正4: API Gateway + Lambda用のアダプター使用
    """
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)