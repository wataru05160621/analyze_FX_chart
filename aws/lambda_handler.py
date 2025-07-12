"""
AWS Lambda用のFXチャート分析ハンドラー（エラー監視強化版）
"""
import json
import asyncio
import logging
import os
import traceback
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Lambda環境でのパッケージパス設定
import sys
sys.path.append('/opt/python')
sys.path.append('/var/task')

# AWS クライアント
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')
secrets_client = boto3.client('secretsmanager')

# Lambda用ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# メトリクス送信関数
def put_metric(metric_name: str, value: float, unit: str = 'Count', dimensions: dict = None):
    """CloudWatchメトリクスを送信"""
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        cloudwatch.put_metric_data(
            Namespace='FXAnalyzer',
            MetricData=[metric_data]
        )
        logger.info(f"メトリクス送信: {metric_name}={value}")
    except Exception as e:
        logger.warning(f"メトリクス送信エラー: {e}")

def send_alert(subject: str, message: str, severity: str = 'ERROR'):
    """SNS経由でアラート送信"""
    try:
        topic_arn = os.environ.get('SNS_ALERT_TOPIC_ARN')
        if not topic_arn:
            logger.warning("SNS_ALERT_TOPIC_ARNが設定されていません")
            return
            
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"[FXAnalyzer {severity}] {subject}",
            Message=message
        )
        logger.info(f"アラート送信: {subject}")
    except Exception as e:
        logger.error(f"アラート送信エラー: {e}")

def get_secrets():
    """AWS Secrets Managerからシークレットを取得"""
    try:
        secret_name = os.environ.get('SECRET_NAME', 'fx-analyzer-secrets')
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"シークレット取得エラー: {e}")
        raise

def lambda_handler(event, context):
    """
    AWS Lambda エントリーポイント（エラー監視強化版）
    """
    start_time = datetime.utcnow()
    execution_id = context.aws_request_id if context else 'local-test'
    
    # 開始メトリクス
    put_metric('LambdaInvocation', 1, dimensions={'ExecutionId': execution_id})
    
    try:
        logger.info(f"Lambda実行開始: {start_time.isoformat()}")
        logger.info(f"実行ID: {execution_id}")
        logger.info(f"Event: {json.dumps(event, default=str)}")
        
        # シークレット取得
        secrets = get_secrets()
        
        # 環境変数設定
        for key, value in secrets.items():
            os.environ[key] = value
        
        # イベントソースの判定
        event_source = _get_event_source(event)
        logger.info(f"イベントソース: {event_source}")
        put_metric('EventSource', 1, dimensions={'Source': event_source})
        
        # FX分析を実行（Lambda軽量版）
        from src.lambda_main import analyze_fx_charts
        result = asyncio.run(analyze_fx_charts())
        
        # 実行時間を計算
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # 成功メトリクス
        put_metric('ExecutionTime', execution_time, 'Seconds')
        put_metric('AnalysisSuccess', 1)
        put_metric('ErrorRate', 0)
        
        if result and result.get("status") == "success":
            put_metric('NotionPageCreated', 1)
            logger.info(f"分析成功: {execution_time:.2f}秒")
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "success",
                    "timestamp": end_time.isoformat(),
                    "execution_time_seconds": execution_time,
                    "execution_id": execution_id,
                    "screenshots_count": len(result.get("screenshots", {})),
                    "analysis_length": len(result.get("analysis", "")),
                    "notion_page_id": result.get("notion_page_id"),
                    "event_source": event_source
                }, ensure_ascii=False)
            }
        else:
            # 分析失敗
            error_msg = result.get("error", "Unknown analysis error") if result else "No result returned"
            put_metric('AnalysisError', 1)
            put_metric('ErrorRate', 1)
            
            send_alert(
                subject="FX分析失敗",
                message=f"実行ID: {execution_id}\nエラー: {error_msg}\n実行時間: {execution_time:.2f}秒",
                severity="ERROR"
            )
            
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "status": "error",
                    "error": error_msg,
                    "timestamp": end_time.isoformat(),
                    "execution_time_seconds": execution_time,
                    "execution_id": execution_id,
                    "event_source": event_source
                }, ensure_ascii=False)
            }
        
    except Exception as e:
        # エラー処理
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        
        # エラーメトリクス
        put_metric('LambdaError', 1)
        put_metric('ErrorRate', 1)
        put_metric('ExecutionTime', execution_time, 'Seconds')
        
        logger.error(f"Lambda実行エラー: {error_msg}")
        logger.error(f"スタックトレース: {error_traceback}")
        
        # 重要なエラーはSNSアラート送信
        if should_send_alert(e):
            send_alert(
                subject="Lambda実行エラー",
                message=f"実行ID: {execution_id}\nエラー: {error_msg}\n実行時間: {execution_time:.2f}秒\n\nスタックトレース:\n{error_traceback}",
                severity="CRITICAL"
            )
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "error": error_msg,
                "timestamp": end_time.isoformat(),
                "execution_time_seconds": execution_time,
                "execution_id": execution_id
            }, ensure_ascii=False)
        }

def should_send_alert(error: Exception) -> bool:
    """エラーがアラート送信対象かどうか判定"""
    critical_errors = [
        'EnvironmentError',
        'ClientError',
        'TimeoutError',
        'ConnectionError'
    ]
    return any(err_type in str(type(error)) for err_type in critical_errors)

def _validate_lambda_environment():
    """Lambda環境の検証"""
    required_env_vars = [
        "OPENAI_API_KEY",
        "NOTION_API_KEY", 
        "NOTION_DATABASE_ID",
        "AWS_S3_BUCKET"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(f"必要な環境変数が不足: {', '.join(missing_vars)}")
    
    logger.info("Lambda環境変数の検証完了")

def _get_event_source(event):
    """イベントソースを判定"""
    if "Records" in event:
        # S3イベント
        if any("s3" in record.get("eventSource", "") for record in event["Records"]):
            return "s3"
        # SNSイベント
        elif any("Sns" in record for record in event["Records"]):
            return "sns"
    elif "source" in event:
        # EventBridge (CloudWatch Events)
        if event["source"] == "aws.events":
            return "eventbridge"
    elif "httpMethod" in event:
        # API Gateway
        return "api_gateway"
    elif "ScheduleExpression" in event:
        # CloudWatch Events (スケジュール)
        return "schedule"
    else:
        return "manual"

# CloudWatch Events用のテストハンドラー
def test_handler(event, context):
    """テスト実行用のハンドラー"""
    logger.info("テストハンドラー実行")
    
    # 簡略化されたテスト実行
    test_event = {
        "source": "test",
        "detail-type": "FX Analysis Test",
        "detail": {
            "test": True
        }
    }
    
    return lambda_handler(test_event, context)