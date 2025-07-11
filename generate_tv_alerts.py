#!/usr/bin/env python3
"""
Phase 1 + TradingViewアラート設定生成
分析結果からTradingViewアラート設定を自動生成する統合スクリプト
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import os

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
load_dotenv('.env')
load_dotenv('.env.phase1')

# 環境変数の一時的な修正
os.environ["BLOG_POST_HOUR"] = "8"
os.environ["WORDPRESS_CATEGORY_USDJPY"] = "4"
os.environ["WORDPRESS_CATEGORY_BTCUSD"] = "5"
os.environ["WORDPRESS_CATEGORY_XAUUSD"] = "6"

from src.phase1_alert_system import SignalGenerator
from src.tradingview_alert_generator import (
    AlertConfiguration,
    TradingViewAlertGenerator,
    PineScriptGenerator
)
from src.logger import setup_logger

logger = setup_logger(__name__)


class Phase1ToTradingView:
    """Phase 1の分析結果をTradingViewアラートに変換"""
    
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.tv_generator = TradingViewAlertGenerator()
        self.pine_generator = PineScriptGenerator()
        
    def process_analysis(self, analysis_text: str, currency_pair: str = "USD/JPY"):
        """分析テキストからTradingViewアラート設定を生成"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"{currency_pair} TradingViewアラート設定生成")
        logger.info(f"{'='*60}")
        
        # 1. Phase 1シグナル生成
        signal = self.signal_generator.generate_trading_signal(analysis_text)
        
        logger.info(f"\n【生成されたシグナル】")
        logger.info(f"アクション: {signal['action']}")
        logger.info(f"エントリー: {signal.get('entry_price', 0)}")
        logger.info(f"損切り: {signal.get('stop_loss', 0)}")
        logger.info(f"利確: {signal.get('take_profit', 0)}")
        logger.info(f"信頼度: {signal['confidence']:.1%}")
        
        if signal['action'] == 'NONE':
            logger.info("\n明確なシグナルがないため、アラート設定をスキップします")
            return None
        
        # 2. アラート設定を作成
        try:
            config = AlertConfiguration.from_phase1_signal(signal, currency_pair)
        except ValueError as e:
            logger.error(f"設定エラー: {e}")
            return None
        
        # 3. TradingViewアラートを生成
        alerts = self.tv_generator.generate_all_alerts(config)
        
        # 4. 設定手順を出力
        instructions = self.tv_generator.export_instructions(alerts, config)
        print("\n" + instructions)
        
        # 5. Pine Scriptを生成
        script = self.pine_generator.generate_script(config)
        
        # 6. ファイルに保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # アラート設定をJSON形式で保存
        import json
        alerts_file = f"tv_alerts_{currency_pair.replace('/', '')}_{timestamp}.json"
        with open(alerts_file, 'w', encoding='utf-8') as f:
            json.dump({
                'currency_pair': currency_pair,
                'signal': signal,
                'alerts': alerts,
                'generated_at': timestamp
            }, f, ensure_ascii=False, indent=2)
        
        # Pine Scriptを保存
        script_file = f"tv_script_{currency_pair.replace('/', '')}_{timestamp}.pine"
        script_path = self.pine_generator.save_script(script, script_file)
        
        # 設定手順をテキストファイルに保存
        instructions_file = f"tv_instructions_{currency_pair.replace('/', '')}_{timestamp}.txt"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        logger.info(f"\n【ファイル生成完了】")
        logger.info(f"アラート設定: {alerts_file}")
        logger.info(f"Pine Script: {script_file}")
        logger.info(f"設定手順: {instructions_file}")
        
        return {
            'config': config,
            'alerts': alerts,
            'script': script,
            'files': {
                'alerts': alerts_file,
                'script': script_file,
                'instructions': instructions_file
            }
        }


async def main():
    """メイン処理"""
    
    print("="*60)
    print("Phase 1 → TradingViewアラート設定生成ツール")
    print("="*60)
    
    converter = Phase1ToTradingView()
    
    # オプション選択
    print("\n実行モードを選択してください:")
    print("1. テストデータで実行")
    print("2. 最新の分析結果を使用")
    print("3. カスタム分析テキストを入力")
    
    choice = input("\n選択 (1-3): ").strip()
    
    if choice == '1':
        # テストデータ
        test_analyses = {
            "USD/JPY": """
            USD/JPYは145.50で強いブレイクアウトを確認しました。
            上昇トレンドが継続する可能性が高く、146.00を目標に、
            145.20を損切りラインとして買いエントリーを推奨します。
            """,
            "EUR/USD": """
            EUR/USDは1.0850で売りシグナルが点灯しています。
            1.0800を目標に、1.0880を損切りラインとして
            売りエントリーを検討してください。
            """
        }
        
        for currency_pair, analysis in test_analyses.items():
            converter.process_analysis(analysis, currency_pair)
            print("\n" + "-"*60 + "\n")
    
    elif choice == '2':
        # 最新の分析結果を読み込む（実装が必要）
        print("\n最新の分析結果を検索中...")
        # TODO: Notionまたはログから最新の分析を取得
        print("※この機能は開発中です")
    
    elif choice == '3':
        # カスタム入力
        currency_pair = input("\n通貨ペア (例: USD/JPY): ").strip()
        print("\n分析テキストを入力してください（Enterを2回押して終了）:")
        
        lines = []
        empty_count = 0
        while True:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        
        analysis_text = "\n".join(lines)
        
        if analysis_text.strip():
            converter.process_analysis(analysis_text, currency_pair)
    
    else:
        print("\n無効な選択です")
    
    print("\n" + "="*60)
    print("処理完了")
    print("="*60)
    
    # 使い方の説明
    print("\n【TradingViewでの設定方法】")
    print("1. 生成された設定手順ファイル（tv_instructions_*.txt）を開く")
    print("2. TradingViewでチャートを開く")
    print("3. 手順に従ってアラートを設定")
    print("\nまたは")
    print("1. Pine Scriptファイル（tv_script_*.pine）を開く")
    print("2. TradingViewのPineエディタにコピー&ペースト")
    print("3. 「チャートに追加」をクリック")


if __name__ == "__main__":
    asyncio.run(main())