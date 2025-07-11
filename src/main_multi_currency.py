"""
マルチ通貨対応メインファイル（ECS用）
AM8:00 - USD/JPY, BTC/USD, XAU/USD分析 + USD/JPYブログ投稿
PM3:00, PM9:00 - USD/JPY分析のみ
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
from .config import (
    ANALYSIS_MODE,
    ENABLE_BLOG_POSTING,
    BLOG_POST_HOUR,
    WORDPRESS_URL,
    WORDPRESS_USERNAME,
    WORDPRESS_PASSWORD,
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    NOTION_API_KEY,
    NOTION_DATABASE_ID
)
from .multi_currency_analyzer_optimized import MultiCurrencyAnalyzerOptimized, CURRENCY_PAIRS
from .chart_generator import ChartGenerator
from .claude_analyzer import ClaudeAnalyzer
from .notion_writer import NotionWriter
from .blog_analyzer import BlogAnalyzer
from .blog_publisher import BlogPublisher
from .logger import setup_logger
from .error_handler import handle_error, ConfigurationError

logger = setup_logger(__name__)

# Phase 1統合
ENABLE_PHASE1 = os.environ.get('ENABLE_PHASE1', 'false').lower() == 'true'
if ENABLE_PHASE1:
    try:
        from .phase1_alert_system import SignalGenerator, TradingViewAlertSystem
        from .phase1_performance_automation import Phase1PerformanceAutomation
        logger.info("Phase 1: FX分析アラートシステムを初期化しました")
    except ImportError as e:
        logger.warning(f"Phase 1モジュールのインポートに失敗: {e}")
        ENABLE_PHASE1 = False

def _validate_configuration():
    """設定の検証"""
    errors = []
    
    # API設定チェック
    if ANALYSIS_MODE == "claude":
        from .config import CLAUDE_API_KEY
        if not CLAUDE_API_KEY or CLAUDE_API_KEY == "your_claude_api_key_here":
            errors.append("CLAUDE_API_KEYが設定されていません")
    
    # Notion設定チェック
    if not NOTION_API_KEY:
        errors.append("NOTION_API_KEYが設定されていません")
    if not NOTION_DATABASE_ID:
        errors.append("NOTION_DATABASE_IDが設定されていません")
    
    if errors:
        error_msg = "設定エラー:\n" + "\n".join(errors)
        raise ConfigurationError(error_msg)

@handle_error(exception_type=Exception, message="マルチ通貨分析で重大なエラーが発生しました", reraise=False)
async def analyze_fx_multi_currency():
    """マルチ通貨FXチャート分析メインプロセス"""
    try:
        logger.info("マルチ通貨FXチャート分析を開始します")
        
        # 環境変数から強制的な時刻を取得（テスト用）
        force_hour = os.getenv("FORCE_HOUR")
        current_hour = int(force_hour) if force_hour else datetime.now().hour
        logger.info(f"実行時刻: {current_hour}時")
        
        # 設定の検証
        _validate_configuration()
        
        # 8時の場合は3通貨分析 + ブログ投稿
        if current_hour == 8:
            logger.info("AM8:00 - 3通貨分析 + ブログ投稿モード")
            
            # 1. マルチ通貨分析（USD/JPY, BTC/USD, XAU/USD）
            logger.info("3通貨の分析を開始します（レート制限対応版）...")
            analyzer = MultiCurrencyAnalyzerOptimized()
            results = await analyzer.analyze_all_pairs_sequential()
            
            # 2. Notionへの保存は各通貨分析後に自動的に実行される
            
            # 3. USD/JPYのブログ投稿
            if ENABLE_BLOG_POSTING and 'USD/JPY' in results and results['USD/JPY'].get('status') == 'success':
                try:
                    logger.info("USD/JPYのブログ投稿を開始...")
                    
                    # 設定の検証
                    if not all([WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD]):
                        logger.warning("WordPress設定が不完全です。ブログ投稿をスキップします。")
                    else:
                        # 既存の分析結果を使用（二重分析を回避）
                        # blog_analyzer = BlogAnalyzer()  # 削除: 二重分析の原因
                        # blog_analysis = blog_analyzer.analyze_for_blog(results['USD/JPY']['screenshots'])  # 削除
                        
                        # 既存の分析結果をブログ用にフォーマット
                        original_analysis = results['USD/JPY']['analysis']
                        
                        # ブログ用のヘッダーとフッターを追加
                        blog_analysis = f"""**本記事は投資判断を提供するものではありません。**FXチャートの分析手法を学習する目的で、現在のチャート状況を解説しています。実際の売買は自己責任で行ってください。

{original_analysis}

---
※このブログ記事は教育目的で作成されています。投資は自己責任でお願いします。"""
                        
                        wordpress_config = {
                            "url": WORDPRESS_URL,
                            "username": WORDPRESS_USERNAME,
                            "password": WORDPRESS_PASSWORD
                        }
                        
                        twitter_config = {
                            "api_key": TWITTER_API_KEY,
                            "api_secret": TWITTER_API_SECRET,
                            "access_token": TWITTER_ACCESS_TOKEN,
                            "access_token_secret": TWITTER_ACCESS_TOKEN_SECRET
                        }
                        
                        publisher = BlogPublisher(wordpress_config, twitter_config)
                        publish_results = publisher.publish_analysis(
                            blog_analysis, 
                            results['USD/JPY']['screenshots']
                        )
                        
                        if publish_results['wordpress_url']:
                            logger.info(f"WordPress投稿成功: {publish_results['wordpress_url']}")
                        if publish_results['twitter_url']:
                            logger.info(f"Twitter投稿成功: {publish_results['twitter_url']}")
                            
                except Exception as e:
                    logger.error(f"ブログ投稿エラー（続行します）: {str(e)}")
            
            # サマリーレポート生成
            summary = analyzer.generate_summary_report(results)
            logger.info(f"\n{summary}")
            
        else:
            # 15時、21時はUSD/JPYのみ分析
            logger.info(f"{current_hour}時 - USD/JPY単独分析モード")
            
            # USD/JPYのみ分析
            generator = ChartGenerator('USDJPY=X')
            screenshot_dir = Path("screenshots")
            screenshot_dir.mkdir(exist_ok=True)
            
            screenshots = generator.generate_multiple_charts(
                timeframes=['5min', '1hour'],
                output_dir=screenshot_dir,
                candle_count=288
            )
            
            # AI分析
            claude_analyzer = ClaudeAnalyzer()
            analysis_result = claude_analyzer.analyze_charts(screenshots)
            
            # Phase 1統合
            if ENABLE_PHASE1:
                try:
                    signal_generator = SignalGenerator()
                    alert_system = TradingViewAlertSystem()
                    performance = Phase1PerformanceAutomation()
                    
                    # シグナル生成
                    signal = signal_generator.generate_trading_signal(analysis_result)
                    
                    if signal['action'] != 'NONE':
                        # アラート送信
                        alert_data = {
                            'signal': signal,
                            'summary': analysis_result
                        }
                        alert = alert_system.send_trade_alert(alert_data)
                        
                        # パフォーマンス記録
                        signal_id = performance.record_signal(signal, {'summary': analysis_result})
                        logger.info(f"Phase 1: シグナル記録 - {signal_id}")
                        
                except Exception as e:
                    logger.error(f"Phase 1エラー: {e}", exc_info=True)
            
            # Notionに保存
            notion = NotionWriter()
            page_id = notion.create_analysis_page(
                title=f"USD/JPY分析_{datetime.now().strftime('%Y%m%d_%H%M')}",
                analysis=analysis_result,
                chart_images=screenshots,
                currency="USD/JPY"
            )
            
            logger.info(f"USD/JPY分析完了。Notionページ: {page_id}")
        
        logger.info("すべての処理が完了しました")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

def main():
    """エントリーポイント"""
    try:
        result = asyncio.run(analyze_fx_multi_currency())
        
        if result["status"] == "success":
            print("\n✅ マルチ通貨FXチャート分析が正常に完了しました")
        else:
            print(f"\n❌ エラーが発生しました: {result['error']}")
            sys.exit(1)
                    
    except Exception as e:
        logger.critical(f"致命的なエラー: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()