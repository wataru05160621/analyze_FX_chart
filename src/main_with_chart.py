"""
FXチャート分析メインモジュール（Python生成チャート版）
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from src.config import (
    TIMEFRAMES,
    USE_WEB_CHATGPT,
    ANALYSIS_MODE,
    SCREENSHOT_DIR,
    NOTION_DATABASE_ID
)
from src.chart_generator import ChartGenerator
from src.chatgpt_analyzer import ChartAnalyzer
from src.chatgpt_web_analyzer import ChatGPTWebAnalyzer
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.error_handler import handle_error, error_recorder, AnalysisError
from src.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger(__name__)

def _validate_configuration():
    """設定の検証"""
    errors = []
    
    # API設定チェック
    if ANALYSIS_MODE == "openai" and not USE_WEB_CHATGPT:
        from src.config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            errors.append("OPENAI_API_KEYが設定されていません")
    elif ANALYSIS_MODE == "claude":
        from src.config import CLAUDE_API_KEY
        if not CLAUDE_API_KEY or CLAUDE_API_KEY == "your_claude_api_key_here":
            errors.append("CLAUDE_API_KEYが設定されていません")
    
    # Notion設定チェック
    from src.config import NOTION_API_KEY, NOTION_DATABASE_ID
    if not NOTION_API_KEY:
        errors.append("NOTION_API_KEYが設定されていません")
    if not NOTION_DATABASE_ID:
        errors.append("NOTION_DATABASE_IDが設定されていません")
    
    if errors:
        error_msg = "設定エラー:\n" + "\n".join(errors)
        raise ValueError(error_msg)

@handle_error(exception_type=Exception, message="FXチャート分析で重大なエラーが発生しました", reraise=False)
async def analyze_fx_charts():
    """FXチャートを分析してNotionに保存する"""
    _validate_configuration()
    
    logger.info("FXチャート分析を開始します")
    
    # 1. チャート生成
    logger.info("Pythonでチャートを生成中...")
    generator = ChartGenerator('USDJPY=X')
    
    try:
        # 複数の時間足でチャート生成（288本のローソク足）
        screenshots = generator.generate_multiple_charts(
            timeframes=list(TIMEFRAMES.keys()),
            output_dir=SCREENSHOT_DIR,
            candle_count=288
        )
        
        if not screenshots:
            raise Exception("チャートの生成に失敗しました")
            
        logger.info(f"生成したチャート: {list(screenshots.keys())}")
        
        # 2. LLMで分析
        if ANALYSIS_MODE == "claude":
            logger.info("Claude 3.5 Sonnet で分析中...")
            analyzer = ClaudeAnalyzer()
            analysis_result = analyzer.analyze_charts(screenshots)
        elif USE_WEB_CHATGPT:
            logger.info("ChatGPT Webプロジェクトで分析中...")
            analyzer = ChatGPTWebAnalyzer()
            await analyzer.setup()
            try:
                # ChatGPT Webのデフォルトプロンプト
                prompt = "プロジェクトファイルを参考に、画像について環境認識、トレードプランの作成をしてください。"
                analysis_result = await analyzer.analyze_charts(screenshots, prompt)
            finally:
                await analyzer.close()
        else:
            logger.info("ChatGPT APIで分析中...")
            analyzer = ChartAnalyzer()
            analysis_result = analyzer.analyze_charts(screenshots)
        
        if not analysis_result:
            raise AnalysisError("分析結果が空です")
            
        logger.info(f"分析完了: {len(analysis_result)}文字")
        
        # 3. Notionに保存
        logger.info("Notionに結果を保存中...")
        notion_writer = NotionWriter()
        
        title = f"FXチャート分析 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        page_id = notion_writer.create_analysis_page(
            title=title,
            analysis=analysis_result,
            chart_images=screenshots
        )
        
        logger.info(f"Notionページを作成しました: {page_id}")
        
    except AnalysisError as e:
        logger.error(f"分析エラーが発生しました: {e}")
        raise
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        raise
    
    logger.info("すべての処理が完了しました")
    
    # エラーサマリーをチェック
    summary = error_recorder.get_summary()
    if summary["total_errors"] > 0:
        logger.warning(f"実行中に{summary['total_errors']}件のエラーが発生しました")
    
    return {
        "status": "success",
        "screenshots": {k: str(v) for k, v in screenshots.items()},
        "analysis": analysis_result[:200] + "..." if len(analysis_result) > 200 else analysis_result,
        "notion_page_id": page_id
    }

def main():
    """メイン関数"""
    try:
        # 非同期処理を実行
        result = asyncio.run(analyze_fx_charts())
        
        # 結果を表示
        if result and result.get("status") == "success":
            print("\n✅ FXチャート分析が正常に完了しました")
            print(f"スクリーンショット: {result['screenshots']}")
            print(f"\n分析結果:\n{result['analysis']}")
        else:
            print("\n❌ FXチャート分析でエラーが発生しました")
            if result and "error" in result:
                print(f"エラー: {result['error']}")
        
        # エラーサマリーを表示
        summary = error_recorder.get_summary()
        if summary["total_errors"] > 0:
            print(f"\nエラーサマリー:")
            print(f"総エラー数: {summary['total_errors']}")
            for error_type, count in summary.get("error_types", {}).items():
                print(f"  - {error_type}: {count}件")
            
    except Exception as e:
        logger.error(f"メイン処理でエラーが発生しました: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main()