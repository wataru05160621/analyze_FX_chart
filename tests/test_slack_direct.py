#!/usr/bin/env python3
"""
Phase 1: Slack通知の直接テスト
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
load_dotenv('.env.phase1')

from src.phase1_alert_system import TradingViewAlertSystem

def send_test_notification():
    """テスト通知を送信"""
    alert_system = TradingViewAlertSystem()
    
    # 現在時刻を含むテストメッセージ
    test_alert = {
        'symbol': 'USD/JPY',
        'action': 'BUY',
        'entry': 145.50,
        'stop_loss': 145.20,
        'take_profit': 146.00,
        'confidence': 0.85,
        'analysis': f'Phase 1 動作確認テスト - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    }
    
    print("Slack通知を送信します...")
    
    try:
        alert_system._send_slack_notification(test_alert)
        print("✅ 送信完了！Slackチャンネルを確認してください。")
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    send_test_notification()