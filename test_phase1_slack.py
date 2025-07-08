#!/usr/bin/env python3
"""
Phase 1: Slack通知の動作確認スクリプト
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
load_dotenv('.env.phase1')

from src.phase1_alert_system import TradingViewAlertSystem, SignalGenerator

def test_slack_notification():
    """Slack通知のテスト"""
    print("=== Slack通知テストを開始 ===\n")
    
    # アラートシステムを初期化
    alert_system = TradingViewAlertSystem()
    
    # テスト用の売買シグナル
    test_alert = {
        'symbol': 'USD/JPY',
        'action': 'BUY',
        'entry': 145.50,
        'stop_loss': 145.20,
        'take_profit': 146.00,
        'confidence': 0.85,
        'analysis': 'Phase 1テスト: 強い上昇トレンドを確認。ブレイクアウト後の買いシグナルです。'
    }
    
    print("以下の内容でSlackに通知を送信します:")
    print(f"通貨ペア: {test_alert['symbol']}")
    print(f"アクション: {test_alert['action']}")
    print(f"エントリー: {test_alert['entry']}")
    print(f"損切り: {test_alert['stop_loss']}")
    print(f"利確: {test_alert['take_profit']}")
    print(f"信頼度: {test_alert['confidence']:.1%}")
    
    try:
        # Slack通知を送信
        alert_system._send_slack_notification(test_alert)
        print("\n✅ Slack通知を送信しました！")
        print("Slackチャンネルを確認してください。")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        return False
    
    return True

def test_signal_generation():
    """シグナル生成のテスト"""
    print("\n=== シグナル生成テストを開始 ===\n")
    
    generator = SignalGenerator()
    
    # テスト用の分析テキスト
    test_analyses = [
        {
            "text": """
            USD/JPYは145.50で強いブレイクアウトを確認しました。
            上昇トレンドが継続する可能性が高く、146.00を目標に、
            145.20を損切りラインとして買いエントリーを推奨します。
            """,
            "expected_action": "BUY"
        },
        {
            "text": """
            下落トレンドが継続しており、145.80での売りシグナルが
            点灯しています。145.50を目標に、146.10を損切りラインと
            して売りエントリーを検討してください。
            """,
            "expected_action": "SELL"
        },
        {
            "text": """
            現在のUSD/JPYは方向感が不明瞭で、レンジ相場となっています。
            明確なトレンドが形成されるまで様子見を推奨します。
            """,
            "expected_action": "NONE"
        }
    ]
    
    for i, test_case in enumerate(test_analyses):
        print(f"テストケース {i+1}:")
        signal = generator.generate_trading_signal(test_case["text"])
        
        print(f"生成されたシグナル: {signal['action']}")
        print(f"期待されるシグナル: {test_case['expected_action']}")
        
        if signal['action'] == test_case['expected_action']:
            print("✅ 成功\n")
        else:
            print("❌ 失敗\n")
            return False
    
    return True

def main():
    """メイン実行関数"""
    print("Phase 1: アラートシステムの動作確認\n")
    
    # シグナル生成テスト
    if not test_signal_generation():
        print("シグナル生成テストに失敗しました")
        sys.exit(1)
    
    # Slack通知テスト
    print("\nSlack通知テストを実行しますか？")
    print("（実際にSlackに通知が送信されます）")
    response = input("実行する場合は 'y' を入力: ")
    
    if response.lower() == 'y':
        if test_slack_notification():
            print("\n🎉 全てのテストが成功しました！")
            print("\n次のステップ:")
            print("1. 本番環境で実行: python src/phase1_integration.py")
            print("2. Cronジョブを設定して定期実行")
            print("3. Phase 2（OANDA デモ取引）の準備")
        else:
            print("\nSlack通知テストに失敗しました")
            print("環境変数とWebhook URLを確認してください")
    else:
        print("\nSlack通知テストをスキップしました")
        print("準備ができたら再度実行してください")

if __name__ == "__main__":
    main()