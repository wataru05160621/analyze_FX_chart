#!/usr/bin/env python3
"""
TradingViewアラート設定生成（シンプル版）
テスト駆動開発で実装した半自動化ツール
"""
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.phase1_alert_system import SignalGenerator
from src.tradingview_alert_generator import (
    AlertConfiguration,
    TradingViewAlertGenerator,
    PineScriptGenerator
)


def main():
    print("="*60)
    print("TradingViewアラート設定生成ツール（半自動化）")
    print("="*60)
    
    # テスト用の分析テキスト
    test_analyses = [
        {
            "currency": "USD/JPY",
            "text": """
            USD/JPYは145.50で強いブレイクアウトを確認しました。
            上昇トレンドが継続する可能性が高く、146.00を目標に、
            145.20を損切りラインとして買いエントリーを推奨します。
            """
        },
        {
            "currency": "EUR/USD",
            "text": """
            EUR/USDは1.0850で売りシグナルが点灯しています。
            1.0800を目標に、1.0880を損切りラインとして
            売りエントリーを検討してください。
            """
        }
    ]
    
    # 各分析を処理
    signal_generator = SignalGenerator()
    tv_generator = TradingViewAlertGenerator()
    pine_generator = PineScriptGenerator()
    
    for analysis in test_analyses:
        print(f"\n【{analysis['currency']}の分析】")
        
        # Phase 1シグナル生成
        signal = signal_generator.generate_trading_signal(analysis['text'])
        
        print(f"アクション: {signal['action']}")
        print(f"エントリー: {signal.get('entry_price', 0)}")
        print(f"損切り: {signal.get('stop_loss', 0)}")
        print(f"利確: {signal.get('take_profit', 0)}")
        print(f"信頼度: {signal['confidence']:.1%}")
        
        if signal['action'] != 'NONE':
            # アラート設定生成
            try:
                config = AlertConfiguration.from_phase1_signal(signal, analysis['currency'])
                alerts = tv_generator.generate_all_alerts(config)
                
                # 設定手順を表示
                instructions = tv_generator.export_instructions(alerts, config)
                print("\n" + instructions)
                
                # Pine Script生成
                script = pine_generator.generate_script(config)
                
                # ファイルに保存
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                currency_safe = analysis['currency'].replace('/', '')
                
                # Pine Script保存
                script_file = f"tv_script_{currency_safe}_{timestamp}.pine"
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(script)
                
                # 設定手順保存
                instructions_file = f"tv_instructions_{currency_safe}_{timestamp}.txt"
                with open(instructions_file, 'w', encoding='utf-8') as f:
                    f.write(instructions)
                
                print(f"\n✅ ファイル生成完了:")
                print(f"  - Pine Script: {script_file}")
                print(f"  - 設定手順: {instructions_file}")
                
            except ValueError as e:
                print(f"\n❌ エラー: {e}")
        else:
            print("\n明確なシグナルがありません")
        
        print("\n" + "-"*60)
    
    print("\n【使い方】")
    print("1. TradingViewで該当通貨ペアのチャートを開く")
    print("2. 生成された設定手順ファイル（tv_instructions_*.txt）の内容に従ってアラートを設定")
    print("\nまたは")
    print("1. TradingViewのPineエディタを開く")
    print("2. Pine Scriptファイル（tv_script_*.pine）の内容をコピー&ペースト")
    print("3. 「チャートに追加」をクリック")
    print("\n✨ テスト駆動開発により高品質な実装を実現しました！")


if __name__ == "__main__":
    main()