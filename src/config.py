"""
設定ファイル
"""
import os
from pathlib import Path

# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent

# API設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Trading View設定
TRADINGVIEW_URL = "https://jp.tradingview.com/chart/"  # デフォルトURL
TRADINGVIEW_CUSTOM_URL = os.getenv("TRADINGVIEW_CUSTOM_URL")  # カスタムチャートURL
CHART_SYMBOL = "USDJPY"
TIMEFRAMES = {
    "5min": "5",
    "1hour": "60"
}

# スクリーンショット設定
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# PDF分析設定
PRICE_ACTION_PDF = PROJECT_ROOT / "doc" / "プライスアクションの原則.pdf"

# 分析プロンプト
ANALYSIS_PROMPT = "プロジェクトファイルを参考に、画像について環境認識、トレードプランの作成をしてください。"

# 分析モード
USE_WEB_CHATGPT = os.getenv("USE_WEB_CHATGPT", "true").lower() == "true"

# ChatGPT設定
CHATGPT_MODEL = "gpt-4o"  # または "gpt-4-vision-preview"
MAX_TOKENS = 2000
TEMPERATURE = 0.7

# ChatGPT Web設定
CHATGPT_EMAIL = os.getenv("CHATGPT_EMAIL")
CHATGPT_PASSWORD = os.getenv("CHATGPT_PASSWORD")
CHATGPT_PROJECT_NAME = os.getenv("CHATGPT_PROJECT_NAME", "FXチャート分析")

# スケジュール設定（cronフォーマット）
SCHEDULE_TIMES = [
    "0 9 * * *",   # 毎日9:00
    "0 15 * * *",  # 毎日15:00
    "0 21 * * *"   # 毎日21:00
]

# ログ設定
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "fx_analysis.log"