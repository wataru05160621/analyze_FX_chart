"""
AWS Lambda用のハンドラー
"""
import json
import asyncio
import logging
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Lambda環境でのパッケージパス設定
import sys
sys.path.append('/opt/python')
sys.path.append('/var/task')

from src.main import analyze_fx_charts
from src.logger import setup_logger

# Lambda用ログ設定
logger = setup_logger("lambda_handler", level=logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda エントリーポイント
    
    Args:
        event: Lambda イベントデータ
        context: Lambda コンテキスト
        
    Returns:
        dict: 実行結果
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Lambda実行開始: {start_time}")
        logger.info(f"Event: {json.dumps(event)}")
        
        # 環境変数の確認
        _validate_lambda_environment()
        
        # イベントソースの判定
        event_source = _get_event_source(event)
        logger.info(f"イベントソース: {event_source}")
        
        # FX分析を実行
        result = asyncio.run(analyze_fx_charts())
        
        # 実行時間を計算
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # 結果を整形
        response = {
            "statusCode": 200 if result["status"] == "success" else 500,
            "body": json.dumps({
                "status": result["status"],
                "timestamp": end_time.isoformat(),
                "execution_time_seconds": execution_time,
                "screenshots_count": len(result.get("screenshots", {})),
                "analysis_length": len(result.get("analysis", "")),
                "event_source": event_source
            }, ensure_ascii=False),
            "headers": {
                "Content-Type": "application/json; charset=utf-8"
            }
        }
        
        if result["status"] == "error":
            response["body"] = json.dumps({
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "timestamp": end_time.isoformat(),
                "execution_time_seconds": execution_time,
                "event_source": event_source
            }, ensure_ascii=False)
        
        logger.info(f"Lambda実行完了: {execution_time:.2f}秒")
        return response
        
    except Exception as e:
        error_msg = f"Lambda実行エラー: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "error": error_msg,
                "timestamp": end_time.isoformat(),
                "execution_time_seconds": execution_time
            }, ensure_ascii=False),
            "headers": {
                "Content-Type": "application/json; charset=utf-8"
            }
        }

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