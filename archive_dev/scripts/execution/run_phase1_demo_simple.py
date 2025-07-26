#!/usr/bin/env python3
"""
Phase 1: シンプルなデモ実行（ロガー依存なし）
"""
import asyncio
from datetime import datetime
from pathlib import Path
import sys
from dotenv import load_dotenv

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
load_dotenv('.env.phase1')

from src.phase1_alert_system import (
    SignalGenerator,
    TradingViewAlertSystem,
    PerformanceTracker
)


async def demo_analysis():
    """シンプルなデモ実行"""
    
    # Phase 1コンポーネントを初期化
    signal_generator = SignalGenerator()
    alert_system = TradingViewAlertSystem()
    performance_tracker = PerformanceTracker()
    
    print("=== Phase 1 シンプルデモ ===\n")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 買いシグナルのテスト
    buy_analysis = """
    USD/JPYは145.50で強いブレイクアウトを確認しました。
    上昇トレンドが継続する可能性が高く、146.00を目標に、
    145.20を損切りラインとして買いエントリーを推奨します。
    """
    
    print("【買いシグナルテスト】")
    print(buy_analysis)
    
    # シグナル生成
    signal = signal_generator.generate_trading_signal(buy_analysis)
    print(f"\n生成されたシグナル: {signal['action']}")
    print(f"エントリー: {signal['entry_price']}")
    print(f"信頼度: {signal['confidence']:.1%}")
    
    if signal['action'] != 'NONE':
        print("\n📈 Slackにアラートを送信します...")
        alert = alert_system.send_trade_alert({
            'signal': signal,
            'summary': 'Phase 1 デモ: 買いシグナルテスト'
        })
        
        record_id = performance_tracker.record_signal(signal)
        print(f"✅ 完了 (記録ID: {record_id[:8]}...)")
    
    await asyncio.sleep(2)
    
    # 売りシグナルのテスト
    print("\n" + "="*50 + "\n")
    
    sell_analysis = """
    下落トレンドが継続しており、145.80での売りシグナルが
    点灯しています。145.50を目標に、146.10を損切りラインと
    して売りエントリーを検討してください。
    """
    
    print("【売りシグナルテスト】")
    print(sell_analysis)
    
    signal = signal_generator.generate_trading_signal(sell_analysis)
    print(f"\n生成されたシグナル: {signal['action']}")
    print(f"エントリー: {signal['entry_price']}")
    print(f"信頼度: {signal['confidence']:.1%}")
    
    if signal['action'] != 'NONE':
        print("\n📉 Slackにアラートを送信します...")
        alert = alert_system.send_trade_alert({
            'signal': signal,
            'summary': 'Phase 1 デモ: 売りシグナルテスト'
        })
        
        record_id = performance_tracker.record_signal(signal)
        print(f"✅ 完了 (記録ID: {record_id[:8]}...)")
    
    print("\n" + "="*50)
    print("\n✅ Phase 1 デモ完了！")
    print("\nSlackチャンネルに2つのアラートが送信されているはずです。")
    print("\n次のステップ:")
    print("1. 本番環境での実行準備")
    print("2. Cronジョブの設定")
    print("3. Phase 2（OANDA API）の準備")


if __name__ == "__main__":
    asyncio.run(demo_analysis())