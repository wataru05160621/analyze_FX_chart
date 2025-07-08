"""
設定ファイル
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent

# API設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Trading View設定
TRADINGVIEW_URL = "https://jp.tradingview.com/chart/"  # デフォルトURL
TRADINGVIEW_CUSTOM_URL = os.getenv("TRADINGVIEW_CUSTOM_URL")  # カスタムチャートURL
TRADINGVIEW_USERNAME = os.getenv("TRADINGVIEW_USERNAME")  # Trading Viewユーザー名
TRADINGVIEW_PASSWORD = os.getenv("TRADINGVIEW_PASSWORD")  # Trading Viewパスワード
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
USE_WEB_CHATGPT_STR = os.getenv("USE_WEB_CHATGPT", "true")
USE_WEB_CHATGPT = USE_WEB_CHATGPT_STR.lower() == "true" if USE_WEB_CHATGPT_STR else True
ANALYSIS_MODE = os.getenv("ANALYSIS_MODE", "openai")  # openai, claude, web_chatgpt

# ChatGPT設定
CHATGPT_MODEL = "gpt-4o"  # または "gpt-4-vision-preview"
MAX_TOKENS = 2000
TEMPERATURE = 0.7

# ChatGPT Web設定
CHATGPT_EMAIL = os.getenv("CHATGPT_EMAIL")
CHATGPT_PASSWORD = os.getenv("CHATGPT_PASSWORD")
CHATGPT_PROJECT_NAME = os.getenv("CHATGPT_PROJECT_NAME", "FXチャート分析")

# スケジュール設定（日本時間）
SCHEDULE_TIMES = [
    {"hour": 8, "minute": 0},   # 8:00 AM JST
    {"hour": 15, "minute": 0},  # 3:00 PM JST
    {"hour": 21, "minute": 0}   # 9:00 PM JST
]

# ログ設定
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "fx_analysis.log"

# WordPress設定
WORDPRESS_URL = os.getenv("WORDPRESS_URL")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD")

# X (Twitter) API設定
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET") 
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# ブログ投稿設定
ENABLE_BLOG_POSTING_STR = os.getenv("ENABLE_BLOG_POSTING", "false")
ENABLE_BLOG_POSTING = ENABLE_BLOG_POSTING_STR.lower() == "true"
BLOG_POST_HOUR = int(os.getenv("BLOG_POST_HOUR", "8"))  # 投稿する分析の時間（JST）

# WordPress タクソノミー設定
WORDPRESS_CATEGORY_USDJPY = int(os.getenv("WORDPRESS_CATEGORY_USDJPY", "0"))
WORDPRESS_CATEGORY_ANALYSIS = int(os.getenv("WORDPRESS_CATEGORY_ANALYSIS", "0"))
WORDPRESS_TAG_DAILY_USDJPY = int(os.getenv("WORDPRESS_TAG_DAILY_USDJPY", "0"))