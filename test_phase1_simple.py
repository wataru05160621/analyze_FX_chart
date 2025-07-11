#!/usr/bin/env python3
"""
Phase 1: シンプルな統合テスト（環境変数問題を回避）
"""
import os
import sys
from pathlib import Path

# 環境変数の一時的な修正
os.environ["BLOG_POST_HOUR"] = "8"
os.environ["WORDPRESS_CATEGORY_USDJPY"] = "4"
os.environ["WORDPRESS_CATEGORY_BTCUSD"] = "5"
os.environ["WORDPRESS_CATEGORY_XAUUSD"] = "6"

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv('.env.phase1')

print("=== Phase 1 統合テスト ===")
print("")

# シグナル生成のテスト
from src.phase1_alert_system import SignalGenerator, TradingViewAlertSystem

generator = SignalGenerator()
alert_system = TradingViewAlertSystem()

# テスト分析
test_analysis = """
USD/JPYは145.50で強いブレイクアウトを確認しました。
日銀政策決定会合の結果を受けて円安が加速しており、
146.00を目標に、145.20を損切りラインとして
買いエントリーを推奨します。
"""

print("【分析内容】")
print(test_analysis)
print("")

# シグナル生成
signal = generator.generate_trading_signal(test_analysis)
print("【生成されたシグナル】")
print(f"アクション: {signal['action']}")
print(f"エントリー: {signal['entry_price']}")
print(f"損切り: {signal['stop_loss']}")
print(f"利確: {signal['take_profit']}")
print(f"信頼度: {signal['confidence']:.1%}")
print("")

# アラート送信
if signal['action'] != 'NONE':
    print("Slackに通知を送信します...")
    try:
        alert_system.send_trade_alert({
            'signal': signal,
            'summary': 'Phase 1 統合テスト'
        })
        print("✅ アラート送信完了")
    except Exception as e:
        print(f"⚠️ エラー: {e}")

print("\n=== テスト完了 ===")
print("\n注意事項:")
print("- Slack Webhook URLが404エラーを返しています")
print("- 新しいWebhook URLを生成する必要があります")
print("- Slack App管理画面から再設定してください")
print("  https://api.slack.com/apps")