"""
Phase 1: 既存のFX分析システムとアラートシステムの統合
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict
import os
import sys

# 既存のモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent))
from src.config import Config
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.phase1_alert_system import (
    SignalGenerator,
    TradingViewAlertSystem,
    PerformanceTracker
)
from src.logger import setup_logger

logger = setup_logger(__name__)


class Phase1FXAnalysisWithAlerts:
    """既存の分析システムにアラート機能を追加"""
    
    def __init__(self):
        self.config = Config()
        self.chart_generator = ChartGenerator(self.config)
        self.analyzer = ClaudeAnalyzer(self.config)
        
        # Phase 1の新機能
        self.signal_generator = SignalGenerator()
        self.alert_system = TradingViewAlertSystem()
        self.performance_tracker = PerformanceTracker()
        
        logger.info("Phase 1: FX分析アラートシステムを初期化しました")
    
    async def analyze_and_alert(self, currency_pair: str = "USD/JPY"):
        """
        チャート分析を実行し、売買シグナルを生成してアラート送信
        
        Args:
            currency_pair: 通貨ペア
            
        Returns:
            分析結果とアラート情報
        """
        try:
            # 1. チャート生成（既存機能）
            logger.info(f"{currency_pair}のチャート生成を開始")
            screenshots = self.chart_generator.generate_all_charts(
                self.chart_generator.mt5_wrapper
            )
            
            if not screenshots:
                logger.error("チャート生成に失敗しました")
                return None
            
            # 2. Claude分析（既存機能）
            logger.info("Claude APIで分析を実行")
            analysis_result = self.analyzer.analyze_charts(screenshots)
            
            if not analysis_result:
                logger.error("分析に失敗しました")
                return None
            
            # 3. シグナル生成（Phase 1新機能）
            logger.info("売買シグナルを生成")
            signal = self.signal_generator.generate_trading_signal(
                analysis_result['analysis']
            )
            
            # 分析結果にシグナルを追加
            analysis_result['signal'] = signal
            
            # 4. アラート送信（Phase 1新機能）
            if signal['action'] != 'NONE' and signal['confidence'] >= 0.7:
                logger.info(f"売買シグナル検出: {signal['action']} (信頼度: {signal['confidence']:.1%})")
                
                alert = self.alert_system.send_trade_alert({
                    'signal': signal,
                    'summary': self._create_summary(analysis_result['analysis'])
                })
                
                # 5. パフォーマンス記録（Phase 1新機能）
                record_id = self.performance_tracker.record_signal(signal)
                logger.info(f"シグナルを記録しました: {record_id}")
                
                analysis_result['alert'] = alert
                analysis_result['record_id'] = record_id
            else:
                logger.info("明確な売買シグナルはありません")
                analysis_result['alert'] = None
            
            # 6. チャート画像をクリーンアップ
            self._cleanup_screenshots(screenshots)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析・アラート処理中にエラー: {e}")
            return None
    
    def _create_summary(self, analysis_text: str) -> str:
        """分析テキストから要約を作成"""
        # 最初の2文を要約として使用
        sentences = analysis_text.split('。')
        summary = '。'.join(sentences[:2]) + '。' if len(sentences) > 1 else analysis_text
        return summary[:200]  # 最大200文字
    
    def _cleanup_screenshots(self, screenshots: Dict[str, Path]):
        """生成したスクリーンショットを削除"""
        for path in screenshots.values():
            try:
                if path.exists():
                    path.unlink()
            except Exception as e:
                logger.warning(f"スクリーンショット削除エラー: {e}")


async def main():
    """Phase 1のメイン実行関数"""
    system = Phase1FXAnalysisWithAlerts()
    
    # 現在時刻を確認
    current_hour = datetime.now().hour
    
    # 8:00, 15:00, 21:00の場合のみ実行
    if current_hour in [8, 15, 21]:
        logger.info(f"定期実行時刻です: {current_hour}:00")
        result = await system.analyze_and_alert()
        
        if result:
            logger.info("分析とアラート送信が完了しました")
            
            # 結果サマリーを表示
            if result.get('alert'):
                print(f"\n=== 売買シグナル ===")
                print(f"アクション: {result['signal']['action']}")
                print(f"エントリー: {result['signal']['entry_price']}")
                print(f"損切り: {result['signal']['stop_loss']}")
                print(f"利確: {result['signal']['take_profit']}")
                print(f"信頼度: {result['signal']['confidence']:.1%}")
            else:
                print("\n明確な売買シグナルはありませんでした")
    else:
        logger.info(f"現在時刻 {current_hour}:00 は実行時刻ではありません")
        
        # テストモードの場合は強制実行
        if os.environ.get('TEST_MODE') == '1':
            logger.info("テストモードで実行します")
            result = await system.analyze_and_alert()
            
            if result:
                print("\n[テストモード] 分析完了")
                if result.get('signal'):
                    print(f"シグナル: {result['signal']['action']}")


if __name__ == "__main__":
    # 環境変数ファイルを読み込み
    from dotenv import load_dotenv
    load_dotenv('.env.phase1')
    
    # メイン処理を実行
    asyncio.run(main())