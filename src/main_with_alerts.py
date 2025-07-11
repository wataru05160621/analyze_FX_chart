"""
統合版メインファイル - Phase 1アラート機能付き
Notion、ブログ、X投稿 + Slackアラート
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

# 環境変数の一時的な修正
os.environ["BLOG_POST_HOUR"] = "8"
os.environ["WORDPRESS_CATEGORY_USDJPY"] = "4"
os.environ["WORDPRESS_CATEGORY_BTCUSD"] = "5" 
os.environ["WORDPRESS_CATEGORY_XAUUSD"] = "6"

from config import *
from multi_currency_analyzer_optimized import MultiCurrencyAnalyzerOptimized, CURRENCY_PAIRS
from chart_generator import ChartGenerator
from claude_analyzer import ClaudeAnalyzer
from notion_writer import NotionWriter
from blog_analyzer import BlogAnalyzer
from blog_publisher import BlogPublisher
from logger import setup_logger
# Phase 1アラート機能
from phase1_alert_system import SignalGenerator, TradingViewAlertSystem, PerformanceTracker

logger = setup_logger(__name__)

async def main():
    """統合版メイン処理"""
    logger.info("=== FX分析システム（統合版）開始 ===")
    
    # 現在時刻を取得（JST）
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} JST")
    
    # Phase 1コンポーネント初期化
    signal_generator = SignalGenerator()
    alert_system = TradingViewAlertSystem()
    performance_tracker = PerformanceTracker()
    
    try:
        # 8時の場合は3通貨分析 + ブログ投稿
        if current_hour == 8:
            logger.info("AM8:00 - 3通貨分析 + ブログ投稿モード")
            analyzer = MultiCurrencyAnalyzerOptimized()
            results = await analyzer.analyze_all_pairs_sequential()
            
            # 各通貨の結果を処理
            for currency, result in results.items():
                if result['success']:
                    # Phase 1: シグナル生成とアラート
                    signal = signal_generator.generate_trading_signal(result['analysis'])
                    if signal['action'] != 'NONE' and signal['confidence'] >= 0.7:
                        logger.info(f"{currency} - 売買シグナル検出: {signal['action']}")
                        alert = alert_system.send_trade_alert({
                            'signal': signal,
                            'summary': f"{currency}: {result['analysis'][:200]}"
                        })
                        record_id = performance_tracker.record_signal(signal)
                        logger.info(f"Slackアラート送信完了 (ID: {record_id})")
            
            # USD/JPYのブログ投稿
            if results.get('USD/JPY', {}).get('success'):
                await analyzer.publish_blog_post(
                    results['USD/JPY']['analysis'],
                    results['USD/JPY']['screenshots']
                )
        
        # 15時、21時の場合はUSD/JPYのみ分析
        elif current_hour in [15, 21]:
            logger.info(f"PM{current_hour}:00 - USD/JPY分析のみモード")
            
            # チャート生成
            generator = ChartGenerator()
            mt5 = generator.mt5_wrapper
            screenshots = generator.generate_all_charts(mt5)
            
            if screenshots:
                # 分析実行
                analyzer = ClaudeAnalyzer()
                analysis = analyzer.analyze_charts(screenshots)
                
                if analysis:
                    # Phase 1: シグナル生成とアラート
                    signal = signal_generator.generate_trading_signal(analysis['analysis'])
                    if signal['action'] != 'NONE' and signal['confidence'] >= 0.7:
                        logger.info(f"USD/JPY - 売買シグナル検出: {signal['action']}")
                        alert = alert_system.send_trade_alert({
                            'signal': signal,
                            'summary': analysis['analysis'][:200]
                        })
                        record_id = performance_tracker.record_signal(signal)
                        logger.info(f"Slackアラート送信完了 (ID: {record_id})")
                    
                    # Notion保存
                    notion_writer = NotionWriter()
                    notion_url = await notion_writer.save_analysis(
                        analysis=analysis['analysis'],
                        screenshots=screenshots,
                        currency_pair='USD/JPY'
                    )
                    logger.info(f"Notion保存完了: {notion_url}")
                    
                # クリーンアップ
                for path in screenshots.values():
                    if path.exists():
                        path.unlink()
                        
        else:
            logger.info(f"実行時刻外です（実行時刻: 8:00, 15:00, 21:00）")
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        
    logger.info("=== FX分析システム（統合版）終了 ===")

if __name__ == "__main__":
    asyncio.run(main())