#!/usr/bin/env python3
"""
AWS ECS用デモトレーダー実行スクリプト
24時間365日自動でデモトレードを実行
"""
import os
import sys
import asyncio
import logging
import boto3
from datetime import datetime
from pathlib import Path

# ログ設定（CloudWatch Logs対応）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # CloudWatch Logsに出力
    ]
)
logger = logging.getLogger(__name__)

# AWS クライアント
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# 環境変数から設定を取得
S3_BUCKET = os.environ.get('S3_BUCKET', 'fx-analysis-phase1')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'phase1-trades')

# プロジェクトルートを追加
sys.path.insert(0, '/app')

async def main():
    """ECS上でのメイン処理"""
    logger.info("=== Phase1 デモトレーダー起動 (AWS ECS) ===")
    logger.info(f"S3バケット: {S3_BUCKET}")
    logger.info(f"DynamoDBテーブル: {DYNAMODB_TABLE}")
    
    try:
        # モジュールインポート
        from src.phase1_demo_trader_aws import Phase1DemoTraderAWS
        
        # AWS対応版デモトレーダー初期化
        trader = Phase1DemoTraderAWS(
            s3_bucket=S3_BUCKET,
            dynamodb_table=DYNAMODB_TABLE
        )
        
        # 24時間365日稼働
        await trader.start_trading()
        
    except Exception as e:
        logger.error(f"致命的エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # エラー通知
        try:
            sns_client = boto3.client('sns')
            topic_arn = os.environ.get('SNS_TOPIC_ARN')
            if topic_arn:
                sns_client.publish(
                    TopicArn=topic_arn,
                    Subject='Phase1 デモトレーダー エラー',
                    Message=f'エラー発生: {str(e)}\n\n{traceback.format_exc()}'
                )
        except:
            pass
        
        # ECSタスク異常終了
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())