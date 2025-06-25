"""
メインの実行ファイル
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
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

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def analyze_fx_charts():
    """FXチャートの分析メインプロセス"""
    try:
        logger.info("FXチャート分析を開始します")
        
        # 1. Trading Viewからチャートを取得
        logger.info("Trading Viewからチャートを取得中...")
        scraper = TradingViewScraper()
        await scraper.setup()
        
        # カスタムURLまたはデフォルトURLを使用
        await scraper.navigate_to_chart(TRADINGVIEW_CUSTOM_URL)
        
        # 複数の時間足でスクリーンショットを取得
        screenshots = await scraper.capture_charts(TIMEFRAMES, SCREENSHOT_DIR)
        await scraper.close()
        
        logger.info(f"取得したスクリーンショット: {list(screenshots.keys())}")
        
        # 2. ChatGPTで分析
        analysis_result = ""
        
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
            await analyzer.close()
        else:
            # API版を使用
            logger.info("ChatGPT APIで分析中...")
            analyzer = ChartAnalyzer()
            analysis_result = analyzer.analyze_charts(screenshots)
        
        logger.info("分析完了")
        
        # 3. Notionに保存
        logger.info("Notionに結果を保存中...")
        notion = NotionWriter()
        notion.create_analysis_page(
            title=f"FX分析_{datetime.now().strftime('%Y%m%d_%H%M')}",
            analysis=analysis_result,
            chart_images=screenshots
        )
        
        logger.info("すべての処理が完了しました")
        
        return {
            "status": "success",
            "screenshots": screenshots,
            "analysis": analysis_result
        }
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    """エントリーポイント"""
    result = asyncio.run(analyze_fx_charts())
    
    if result["status"] == "success":
        print("\n✅ FXチャート分析が正常に完了しました")
        print(f"スクリーンショット: {result['screenshots']}")
        print(f"\n分析結果:\n{result['analysis'][:500]}...")
    else:
        print(f"\n❌ エラーが発生しました: {result['error']}")

if __name__ == "__main__":
    main()