"""
AWS Lambda用ハンドラー
EventBridgeからの定時実行に対応
"""
import json
import boto3
import os
from datetime import datetime
import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS クライアント
ecs_client = boto3.client('ecs')
ssm_client = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Lambda関数のメインハンドラー
    EventBridgeから呼び出される
    """
    try:
        # イベントから実行タイプを判定
        execution_type = event.get('execution_type', 'full')
        session_name = event.get('session_name', 'アジアセッション')
        
        logger.info(f"実行開始: タイプ={execution_type}, セッション={session_name}")
        
        # ECSタスクの起動
        response = run_ecs_task(execution_type, session_name)
        
        logger.info(f"ECSタスク起動成功: {response['tasks'][0]['taskArn']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'ECS task started successfully',
                'taskArn': response['tasks'][0]['taskArn'],
                'execution_type': execution_type,
                'session_name': session_name
            })
        }
        
    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        
        # Slack通知
        send_error_notification(str(e))
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def run_ecs_task(execution_type, session_name):
    """
    ECSタスクを起動
    """
    # 環境変数または Parameter Store から設定を取得
    cluster_name = os.environ.get('ECS_CLUSTER_NAME', 'fx-analysis-cluster')
    task_definition = os.environ.get('ECS_TASK_DEFINITION', 'fx-analysis-task')
    subnet_ids = os.environ.get('SUBNET_IDS', '').split(',')
    security_group_id = os.environ.get('SECURITY_GROUP_ID')
    
    # コンテナの環境変数を設定
    container_overrides = {
        'containerOverrides': [
            {
                'name': 'fx-analysis-container',
                'environment': [
                    {
                        'name': 'EXECUTION_TYPE',
                        'value': execution_type
                    },
                    {
                        'name': 'SESSION_NAME',
                        'value': session_name
                    },
                    {
                        'name': 'FORCE_HOUR',
                        'value': str(datetime.now().hour)
                    }
                ]
            }
        ]
    }
    
    # ECSタスクを実行
    response = ecs_client.run_task(
        cluster=cluster_name,
        taskDefinition=task_definition,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': subnet_ids,
                'securityGroups': [security_group_id],
                'assignPublicIp': 'ENABLED'
            }
        },
        overrides=container_overrides
    )
    
    return response

def send_error_notification(error_message):
    """
    エラー時のSlack通知
    """
    try:
        # Parameter Store からWebhook URLを取得
        webhook_url = ssm_client.get_parameter(
            Name='/fx-analysis/slack-webhook-url',
            WithDecryption=True
        )['Parameter']['Value']
        
        import urllib3
        http = urllib3.PoolManager()
        
        message = {
            'text': f'*⚠️ FX分析 Lambda エラー*\n'
                   f'時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                   f'エラー: {error_message}'
        }
        
        response = http.request(
            'POST',
            webhook_url,
            body=json.dumps(message).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        logger.error(f"Slack通知エラー: {str(e)}")