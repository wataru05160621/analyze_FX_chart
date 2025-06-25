"""
メインの実行ファイル
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import sys
from .config import (
    USE_WEB_CHATGPT,
    TRADINGVIEW_CUSTOM_URL,
    TIMEFRAMES,
    SCREENSHOT_DIR,
    ANALYSIS_PROMPT,
    CHATGPT_EMAIL,
    CHATGPT_PASSWORD,
    CHATGPT_PROJECT_NAME
)
from .tradingview_scraper import TradingViewScraper
from .chatgpt_web_analyzer import ChatGPTWebAnalyzer
from .chatgpt_analyzer import ChartAnalyzer
from .notion_writer import NotionWriter
from .logger import setup_logger, log_function_call
from .error_handler import (
    handle_error, 
    error_recorder,
    ChartCaptureError,
    AnalysisError,
    NotionUploadError,
    ConfigurationError
)

# ログ設定
logger = setup_logger(__name__)

def _validate_configuration():
    """設定の検証"""
    required_vars = {}
    
    # 基本設定のチェック
    if not ANALYSIS_PROMPT:
        required_vars["ANALYSIS_PROMPT"] = ANALYSIS_PROMPT
    if not SCREENSHOT_DIR:
        required_vars["SCREENSHOT_DIR"] = SCREENSHOT_DIR
    
    # 分析モードに応じたチェック
    if USE_WEB_CHATGPT:
        if not CHATGPT_EMAIL:
            required_vars["CHATGPT_EMAIL"] = CHATGPT_EMAIL
        if not CHATGPT_PASSWORD:
            required_vars["CHATGPT_PASSWORD"] = CHATGPT_PASSWORD
        if not CHATGPT_PROJECT_NAME:
            required_vars["CHATGPT_PROJECT_NAME"] = CHATGPT_PROJECT_NAME
    else:
        from .config import OPENAI_API_KEY
        if not OPENAI_API_KEY or OPENAI_API_KEY == "test_key_for_debug":
            required_vars["OPENAI_API_KEY"] = "valid API key"
    
    if required_vars:
        raise ConfigurationError(f"必要な設定が不足しています: {', '.join(required_vars.keys())}")

@handle_error(exception_type=Exception, message="FXチャート分析で重大なエラーが発生しました", reraise=False)
@log_function_call
async def analyze_fx_charts():
    """FXチャートの分析メインプロセス"""
    try:
        logger.info("FXチャート分析を開始します")
        
        # 設定の検証（デバッグモードではスキップ）
        if "--debug" not in sys.argv:
            _validate_configuration()
        
        # 1. Trading Viewからチャートを取得
        logger.info("Trading Viewからチャートを取得中...")
        screenshots = {}
        scraper = None
        
        try:
            scraper = TradingViewScraper()
            await scraper.setup()
            
            # カスタムURLまたはデフォルトURLを使用
            await scraper.navigate_to_chart(TRADINGVIEW_CUSTOM_URL)
            
            # 複数の時間足でスクリーンショットを取得
            screenshots = await scraper.capture_charts(TIMEFRAMES, SCREENSHOT_DIR)
            
            if not screenshots:
                raise ChartCaptureError("チャートのスクリーンショットを取得できませんでした")
                
            logger.info(f"取得したスクリーンショット: {list(screenshots.keys())}")
            
        except Exception as e:
            error_recorder.record(e, {"stage": "chart_capture"})
            raise ChartCaptureError(f"チャート取得エラー: {str(e)}")
        finally:
            if scraper:
                await scraper.close()
        
        # 2. ChatGPTで分析
        analysis_result = ""
        analyzer = None
        
        try:
            if USE_WEB_CHATGPT:
                # Web版ChatGPTを使用（プロジェクト機能を利用）
                logger.info("ChatGPT Webプロジェクトで分析中...")
                analyzer = ChatGPTWebAnalyzer(
                    email=CHATGPT_EMAIL,
                    password=CHATGPT_PASSWORD,
                    project_name=CHATGPT_PROJECT_NAME
                )
                await analyzer.setup()
                analysis_result = await analyzer.analyze_charts(screenshots, ANALYSIS_PROMPT)
            else:
                # API版を使用
                logger.info("ChatGPT APIで分析中...")
                analyzer = ChartAnalyzer()
                analysis_result = analyzer.analyze_charts(screenshots)
            
            if not analysis_result:
                raise AnalysisError("分析結果が空です")
                
            logger.info(f"分析完了: {len(analysis_result)}文字")
            
        except Exception as e:
            error_recorder.record(e, {"stage": "analysis", "use_web": USE_WEB_CHATGPT})
            raise AnalysisError(f"分析エラー: {str(e)}")
        finally:
            if analyzer and hasattr(analyzer, 'close') and callable(getattr(analyzer, 'close', None)):
                try:
                    close_method = getattr(analyzer, 'close')
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                except Exception as e:
                    logger.debug(f"Analyzer closeエラー: {e}")
        
        # 3. Notionに保存
        try:
            logger.info("Notionに結果を保存中...")
            notion = NotionWriter()
            page_id = notion.create_analysis_page(
                title=f"FX分析_{datetime.now().strftime('%Y%m%d_%H%M')}",
                analysis=analysis_result,
                chart_images=screenshots
            )
            
            logger.info(f"Notionページを作成しました: {page_id}")
            
        except Exception as e:
            error_recorder.record(e, {"stage": "notion_upload"})
            # Notionエラーは致命的ではないので、エラーを記録して続行
            logger.error(f"Notion保存エラー（続行します）: {str(e)}")
        
        logger.info("すべての処理が完了しました")
        
        # エラーサマリーをログに出力
        error_summary = error_recorder.get_summary()
        if error_summary["total_errors"] > 0:
            logger.warning(f"実行中に{error_summary['total_errors']}件のエラーが発生しました")
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "analysis": analysis_result
        }
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        error_recorder.record(e, {"stage": "main"})
        
        return {
            "status": "error",
            "error": str(e),
            "error_summary": error_recorder.get_summary()
        }

def main():
    """エントリーポイント"""
    try:
        # コマンドライン引数の処理
        if "--debug" in sys.argv:
            setup_logger(__name__, level=logging.DEBUG)
            
        result = asyncio.run(analyze_fx_charts())
        
        if result["status"] == "success":
            print("\n✅ FXチャート分析が正常に完了しました")
            print(f"スクリーンショット: {result['screenshots']}")
            print(f"\n分析結果:\n{result['analysis'][:500]}...")
        else:
            print(f"\n❌ エラーが発生しました: {result['error']}")
            if "error_summary" in result:
                summary = result["error_summary"]
                print(f"\nエラーサマリー:")
                print(f"総エラー数: {summary['total_errors']}")
                for error_type, count in summary.get("error_types", {}).items():
                    print(f"  - {error_type}: {count}件")
                    
    except Exception as e:
        logger.critical(f"致命的なエラー: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()