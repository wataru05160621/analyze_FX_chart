"""
Phase 1 アラートシステムのテスト
"""
import asyncio
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.phase1_alert_system import (
    SignalGenerator,
    TradingViewAlertSystem,
    PerformanceTracker
)

def test_alert_system():
    """アラートシステムのテスト"""
    # ダミーの分析結果
    dummy_analysis = """
    USD/JPYは現在161.50円付近で推移しています。
    4時間足チャートでは上昇トレンドの中での押し目形成が見られ、
    161.00円のサポートラインで反発の兆しがあります。
    
    【買いシグナル】
    - エントリー: 161.50円
    - ストップロス: 161.00円
    - テイクプロフィット: 162.50円
    
    RSIは45で売られ過ぎ圏から反発、MACDもゴールデンクロスを形成しつつあります。
    """
    
    # シグナル生成
    signal_generator = SignalGenerator()
    signal = signal_generator.generate_trading_signal(dummy_analysis)
    
    if signal:
        print(f"\n=== 生成されたシグナル ===")
        print(f"アクション: {signal['action']}")
        print(f"エントリー: {signal['entry_price']}")
        print(f"損切り: {signal['stop_loss']}")
        print(f"利確: {signal['take_profit']}")
        print(f"信頼度: {signal['confidence']:.1%}")
        
        # アラート送信
        alert_system = TradingViewAlertSystem()
        alert_result = alert_system.send_trade_alert({
            'signal': signal,
            'summary': 'テスト: USD/JPYで買いシグナルが発生しました。161.00円のサポートで反発の兆し。'
        })
        
        print(f"\n=== アラート送信結果 ===")
        print(f"Slack: {'✓' if alert_result.get('slack', {}).get('success') else '✗'}")
        print(f"メール: {'✓' if alert_result.get('email', {}).get('success') else '✗'}")
        
        # パフォーマンス記録
        tracker = PerformanceTracker()
        record_id = tracker.record_signal(signal)
        print(f"\nパフォーマンス記録ID: {record_id}")
    else:
        print("シグナルは生成されませんでした")

if __name__ == "__main__":
    # 環境変数読み込み
    from dotenv import load_dotenv
    load_dotenv('.env.phase1')
    
    test_alert_system()