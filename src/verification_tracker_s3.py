"""
検証日数トラッカー（S3版）
Phase1開始からの経過日数を追跡
"""
import os
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class VerificationTracker:
    """検証日数を追跡するクラス（S3版）"""
    
    def __init__(self, bucket_name: str = None, key: str = "verification/phase1_start_date.json"):
        self.bucket_name = bucket_name or os.environ.get('S3_BUCKET_NAME', 'fx-analyzer-charts-ecs-prod-455931011903')
        self.key = key
        self.s3_client = boto3.client('s3')
        self.start_date = self._load_start_date()
    
    def _load_start_date(self) -> datetime:
        """S3から開始日を読み込み（なければ今日を開始日として保存）"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"開始日をS3から読み込み: {data['start_date']}")
            return datetime.fromisoformat(data['start_date'])
        except self.s3_client.exceptions.NoSuchKey:
            # 初回は今日を開始日として保存
            logger.info("開始日が未設定のため、今日を開始日として設定")
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            self._save_start_date(start_date)
            return start_date
        except Exception as e:
            logger.error(f"開始日の読み込みエラー: {e}")
            # エラー時はデフォルトの開始日を使用
            return datetime(2025, 1, 10, 0, 0, 0)  # 2025年1月10日をデフォルト開始日とする
    
    def _save_start_date(self, start_date: datetime):
        """開始日をS3に保存"""
        try:
            data = {
                'start_date': start_date.isoformat(),
                'phase': 'Phase1',
                'description': 'FXスキャルピング検証プロジェクト',
                'created_at': datetime.now().isoformat()
            }
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.key,
                Body=json.dumps(data, ensure_ascii=False, indent=2),
                ContentType='application/json'
            )
            logger.info(f"開始日をS3に保存: {start_date.isoformat()}")
        except Exception as e:
            logger.error(f"開始日の保存エラー: {e}")
    
    def get_verification_day(self) -> int:
        """検証開始からの日数を取得"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days = (today - self.start_date).days + 1  # 開始日を1日目とする
        return days
    
    def get_verification_text(self) -> str:
        """検証日数のテキストを取得"""
        days = self.get_verification_day()
        return f"検証{days}日目"
    
    def get_progress_percentage(self, total_days: int = 90) -> float:
        """Phase1（90日）の進捗率を取得"""
        days = self.get_verification_day()
        return min(100, (days / total_days) * 100)
    
    def get_phase_info(self) -> Dict:
        """現在のフェーズ情報を取得"""
        days = self.get_verification_day()
        
        if days <= 90:
            phase = "Phase1"
            phase_days = days
            phase_total = 90
            description = "データ収集・検証期間"
        elif days <= 180:
            phase = "Phase2"
            phase_days = days - 90
            phase_total = 90
            description = "ブログ収益化期間"
        else:
            phase = "Phase3"
            phase_days = days - 180
            phase_total = None
            description = "AIシグナルサービス期間"
        
        return {
            'current_phase': phase,
            'total_days': days,
            'phase_days': phase_days,
            'phase_total': phase_total,
            'description': description,
            'start_date': self.start_date.strftime('%Y年%m月%d日')
        }
    
    def reset_start_date(self, new_date: datetime = None):
        """開始日をリセット（テスト用）"""
        if new_date is None:
            new_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.start_date = new_date
        self._save_start_date(new_date)

# グローバルインスタンス
_tracker = None

def get_tracker() -> VerificationTracker:
    """シングルトンのトラッカーインスタンスを取得"""
    global _tracker
    if _tracker is None:
        _tracker = VerificationTracker()
    return _tracker