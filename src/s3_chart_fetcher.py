"""
S3からチャート画像を取得するモジュール
Lambda環境用
"""
import os
import boto3
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class S3ChartFetcher:
    """S3からチャート画像を取得するクラス"""
    
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or os.environ.get('S3_BUCKET_NAME', 'fx-analyzer-charts-ecs-prod-455931011903')
        self.s3_client = boto3.client('s3')
        
    def fetch_latest_charts(self, symbol: str = "USDJPY", timeframes: list = None) -> list:
        """最新のチャート画像をS3から取得"""
        if timeframes is None:
            timeframes = ['5min', '1hour', '4hour', '1day']
            
        charts = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # S3から最新のチャート画像を検索
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"charts/{symbol}/",
                MaxKeys=100
            )
            
            if 'Contents' not in response:
                logger.warning("S3にチャート画像が見つかりません")
                return charts
            
            # 最新の画像を取得
            objects = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
            
            for timeframe in timeframes:
                # 各時間枠の最新画像を探す
                for obj in objects:
                    key = obj['Key']
                    if timeframe in key and key.endswith('.png'):
                        # /tmpディレクトリに画像を保存
                        local_path = f"/tmp/{Path(key).name}"
                        
                        logger.info(f"S3から画像を取得: {key}")
                        self.s3_client.download_file(
                            self.bucket_name,
                            key,
                            local_path
                        )
                        
                        charts.append({
                            'timeframe': timeframe,
                            'path': local_path,
                            's3_key': key,
                            'timestamp': obj['LastModified']
                        })
                        break
                        
            logger.info(f"取得したチャート数: {len(charts)}")
            return charts
            
        except Exception as e:
            logger.error(f"S3からのチャート取得エラー: {e}")
            return charts
    
    def upload_chart(self, local_path: str, s3_key: str):
        """チャート画像をS3にアップロード"""
        try:
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'image/png'}
            )
            logger.info(f"チャートをS3にアップロード: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"S3へのアップロードエラー: {e}")
            return False