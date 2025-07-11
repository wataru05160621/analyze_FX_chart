#!/usr/bin/env python3
"""
スケジュール実行スクリプト
- 8時: ブログ、X、Notion投稿
- 15時: Notion投稿のみ
- 21時: Notion投稿のみ
"""
import os
import sys
import schedule
import time
from datetime import datetime
from pathlib import Path
import logging

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduled_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
def load_env():
    """環境変数を読み込み"""
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                if '#' in line:
                    line = line.split('#')[0].strip()
                key, value = line.strip().split('=', 1)
                if value and value not in ['your_value_here', 'your_api_key_here']:
                    os.environ[key] = value

    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# モジュールインポート
def import_modules():
    """必要なモジュールをインポート"""
    global ChartGenerator, ClaudeAnalyzer, NotionWriter, NotionAnalyzer, BlogPublisher, Phase1NotificationSystem
    
    from src.chart_generator import ChartGenerator
    from src.claude_analyzer import ClaudeAnalyzer
    from src.notion_writer import NotionWriter
    from src.notion_analyzer import NotionAnalyzer
    from src.blog_publisher import BlogPublisher
    from src.phase1_notification import Phase1NotificationSystem

def execute_analysis(include_blog=False, session_name=""):
    """
    分析を実行
    Args:
        include_blog: ブログとX投稿を含むか
        session_name: セッション名（アジア/ロンドン/NY）
    """
    try:
        logger.info(f"=== 分析実行開始 {'(フル投稿)' if include_blog else '(Notionのみ)'} ===")
        logger.info(f"セッション: {session_name}")
        
        # 1. チャート生成
        logger.info("チャート生成中...")
        generator = ChartGenerator('USDJPY=X')
        output_dir = Path('screenshots') / f"scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        screenshots = generator.generate_multiple_charts(
            timeframes=['5min', '1hour'],
            output_dir=output_dir,
            candle_count=288
        )
        logger.info(f"チャート生成完了: {output_dir}")
        
        # 2. Claude分析
        logger.info("Claude分析実行中...")
        analyzer = ClaudeAnalyzer()
        analysis = analyzer.analyze_charts(screenshots)
        logger.info(f"分析完了: {len(analysis)}文字")
        
        # 3. Notion投稿（常に実行）
        logger.info("Notion投稿中...")
        notion_analyzer = NotionAnalyzer()
        detailed_analysis = notion_analyzer.create_detailed_analysis(analysis)
        
        writer = NotionWriter()
        page_id = writer.create_analysis_page(
            f"USD/JPY分析 {session_name} {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            detailed_analysis,
            screenshots,
            "USD/JPY"
        )
        logger.info(f"Notion投稿成功: {page_id}")
        
        # 4. ブログとX投稿（8時のみ）
        if include_blog:
            logger.info("WordPress投稿中...")
            blog_content = f"""{analysis}

---
※このブログ記事は教育目的で作成されています。投資は自己責任でお願いします。
※分析手法: Bob Volman「Forex Price Action Scalping」メソッド"""
            
            wp_config = {
                'url': os.environ['WORDPRESS_URL'],
                'username': os.environ['WORDPRESS_USERNAME'],
                'password': os.environ['WORDPRESS_PASSWORD']
            }
            
            tw_config = {
                'api_key': os.environ.get('TWITTER_API_KEY', ''),
                'api_secret': os.environ.get('TWITTER_API_SECRET', ''),
                'access_token': os.environ.get('TWITTER_ACCESS_TOKEN', ''),
                'access_token_secret': os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', '')
            }
            
            publisher = BlogPublisher(wp_config, tw_config)
            results = publisher.publish_analysis(blog_content, screenshots)
            
            if results.get('wordpress_url'):
                logger.info(f"WordPress投稿成功: {results['wordpress_url']}")
                
                # X投稿
                if results.get('twitter_url'):
                    logger.info(f"X投稿成功: {results['twitter_url']}")
                else:
                    # 手動でX投稿を試みる
                    twitter_url = publisher.publish_to_twitter(analysis, results['wordpress_url'])
                    if twitter_url:
                        logger.info(f"X投稿成功: {twitter_url}")
        
        # 5. Slack通知
        logger.info("Slack通知送信中...")
        try:
            notification = Phase1NotificationSystem()
            notification.send_completion_notification(
                "USD/JPY",
                {
                    'analysis': analysis[:500],
                    'chart_paths': screenshots,
                    'session': session_name
                }
            )
            logger.info("Slack通知送信完了")
        except Exception as e:
            logger.error(f"Slackエラー: {e}")
            # 直接Webhook送信
            import requests
            webhook = os.environ.get('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/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')
            message = {
                "text": f"*FX分析完了 ({session_name})*\n"
                       f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                       f"投稿: {'全プラットフォーム' if include_blog else 'Notionのみ'}"
            }
            requests.post(webhook, json=message)
        
        logger.info("=== 分析実行完了 ===\n")
        
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # エラー通知
        try:
            import requests
            webhook = os.environ.get('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/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')
            message = {
                "text": f"*⚠️ FX分析エラー*\n"
                       f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                       f"エラー: {str(e)}"
            }
            requests.post(webhook, json=message)
        except:
            pass

# スケジュールジョブ
def job_8am():
    """8時実行: フル投稿"""
    logger.info("8時の定期実行開始")
    execute_analysis(include_blog=True, session_name="アジアセッション")

def job_3pm():
    """15時実行: Notionのみ"""
    logger.info("15時の定期実行開始")
    execute_analysis(include_blog=False, session_name="ロンドンセッション")

def job_9pm():
    """21時実行: Notionのみ"""
    logger.info("21時の定期実行開始")
    execute_analysis(include_blog=False, session_name="NYセッション")

def is_weekday():
    """平日かどうかを判定"""
    return datetime.now().weekday() < 5  # 月曜(0)から金曜(4)

def run_if_weekday(job_func):
    """平日のみ実行するラッパー"""
    def wrapper():
        if is_weekday():
            job_func()
        else:
            logger.info(f"週末のため実行をスキップ: {job_func.__name__}")
    return wrapper

def main():
    """メイン実行"""
    logger.info("=== スケジュール実行開始 ===")
    logger.info("実行時間:")
    logger.info("- 08:00: ブログ、X、Notion投稿")
    logger.info("- 15:00: Notion投稿のみ")
    logger.info("- 21:00: Notion投稿のみ")
    logger.info("※平日のみ実行\n")
    
    # 環境変数読み込み
    load_env()
    
    # モジュールインポート
    import_modules()
    
    # スケジュール設定
    schedule.every().day.at("08:00").do(run_if_weekday(job_8am))
    schedule.every().day.at("15:00").do(run_if_weekday(job_3pm))
    schedule.every().day.at("21:00").do(run_if_weekday(job_9pm))
    
    # テスト実行オプション
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("テストモード: 即座に実行")
        if len(sys.argv) > 2:
            if sys.argv[2] == "full":
                job_8am()
            elif sys.argv[2] == "notion":
                job_3pm()
        else:
            job_8am()  # デフォルトはフル実行
        return
    
    # スケジュール実行ループ
    logger.info("スケジュール待機中...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
        except KeyboardInterrupt:
            logger.info("スケジュール実行を終了します")
            break
        except Exception as e:
            logger.error(f"スケジュールエラー: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()