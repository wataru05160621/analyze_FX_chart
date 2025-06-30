"""
メインの実行ファイル（Python生成チャート版）
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import sys
from .config import (
    USE_WEB_CHATGPT,
    TIMEFRAMES,
    SCREENSHOT_DIR,
    ANALYSIS_PROMPT,
    CHATGPT_EMAIL,
    CHATGPT_PASSWORD,
    CHATGPT_PROJECT_NAME,
    ANALYSIS_MODE
)
from .chart_generator import ChartGenerator
from .chatgpt_web_analyzer import ChatGPTWebAnalyzer
from .chatgpt_analyzer import ChartAnalyzer
from .claude_analyzer import ClaudeAnalyzer
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
    errors = []
    
    # API設定チェック
    if ANALYSIS_MODE == "openai" and not USE_WEB_CHATGPT:
        from .config import OPENAI_API_KEY
        if not OPENAI_API_KEY or OPENAI_API_KEY == "test_key_for_debug":
            errors.append("OPENAI_API_KEYが設定されていません")
    elif ANALYSIS_MODE == "claude":
        from .config import CLAUDE_API_KEY
        if not CLAUDE_API_KEY or CLAUDE_API_KEY == "your_claude_api_key_here":
            errors.append("CLAUDE_API_KEYが設定されていません")
    
    # Notion設定チェック
    from .config import NOTION_API_KEY, NOTION_DATABASE_ID
    if not NOTION_API_KEY:
        errors.append("NOTION_API_KEYが設定されていません")
    if not NOTION_DATABASE_ID:
        errors.append("NOTION_DATABASE_IDが設定されていません")
    
    if errors:
        error_msg = "設定エラー:\n" + "\n".join(errors)
        raise ConfigurationError(error_msg)

@handle_error(exception_type=Exception, message="FXチャート分析で重大なエラーが発生しました", reraise=False)
@log_function_call
async def analyze_fx_charts():
    """FXチャートの分析メインプロセス（Python生成チャート版）"""
    try:
        logger.info("FXチャート分析を開始します")
        
        # 設定の検証（デバッグモードではスキップ）
        if "--debug" not in sys.argv:
            _validate_configuration()
        
        # 1. Pythonでチャートを生成
        logger.info("Pythonでチャートを生成中...")
        screenshots = {}
        
        try:
            generator = ChartGenerator('USDJPY=X')
            
            # 複数の時間足でチャート生成（288本のローソク足）
            screenshots = generator.generate_multiple_charts(
                timeframes=list(TIMEFRAMES.keys()),
                output_dir=SCREENSHOT_DIR,
                candle_count=288
            )
            
            if not screenshots:
                raise ChartCaptureError("チャートの生成に失敗しました")
                
            logger.info(f"生成したチャート: {list(screenshots.keys())}")
            
        except Exception as e:
            error_recorder.record(e, {"stage": "chart_generation"})
            logger.error(f"チャート生成に失敗しました: {str(e)}")
            raise  # エラーを再発生させてタスクを停止
        
        # 2. LLMで分析
        analysis_result = ""
        analyzer = None
        
        try:
            if ANALYSIS_MODE == "claude":
                logger.info("Claude 3.5 Sonnet で分析中...")
                analyzer = ClaudeAnalyzer()
                analysis_result = analyzer.analyze_charts(screenshots)
            elif USE_WEB_CHATGPT:
                # Web版ChatGPTを使用（プロジェクト機能を利用）
                logger.info("ChatGPT Webプロジェクトで分析中...")
                analyzer = ChatGPTWebAnalyzer(
                    email=CHATGPT_EMAIL,
                    password=CHATGPT_PASSWORD,
                    project_name=CHATGPT_PROJECT_NAME
                )
                await analyzer.setup()
                # ChatGPT Webのデフォルトプロンプト
                prompt = "プロジェクトファイルを参考に、画像について環境認識、トレードプランの作成をしてください。"
                analysis_result = await analyzer.analyze_charts(screenshots, prompt)
            else:
                # API版を使用
                logger.info("ChatGPT APIで分析中...")
                analyzer = ChartAnalyzer()
                analysis_result = analyzer.analyze_charts(screenshots)
            
            if not analysis_result:
                raise AnalysisError("分析結果が空です")
                
            logger.info(f"分析完了: {len(analysis_result)}文字")
            
        except Exception as e:
            error_recorder.record(e, {"stage": "analysis", "mode": ANALYSIS_MODE})
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
            sys.exit(1)  # エラー時にタスクを失敗させる
                    
    except Exception as e:
        logger.critical(f"致命的なエラー: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()