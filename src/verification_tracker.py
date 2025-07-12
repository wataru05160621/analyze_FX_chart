"""
検証日数トラッカー
Phase1開始からの経過日数を追跡
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

class VerificationTracker:
    """検証日数を追跡するクラス"""
    
    def __init__(self, data_file: str = "phase1_start_date.json"):
        # Lambda環境では/tmpディレクトリを使用
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            self.data_file = Path(f"/tmp/{data_file}")
        else:
            self.data_file = Path(data_file)
        self.start_date = self._load_start_date()
    
    def _load_start_date(self) -> datetime:
        """開始日を読み込み（なければ今日を開始日として保存）"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data['start_date'])
        else:
            # 初回は今日を開始日として保存
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            self._save_start_date(start_date)
            return start_date
    
    def _save_start_date(self, start_date: datetime):
        """開始日を保存"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'start_date': start_date.isoformat(),
                'phase': 'Phase1',
                'description': 'FXスキャルピング検証プロジェクト'
            }, f, ensure_ascii=False, indent=2)
    
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