#!/usr/bin/env python3
"""
ECSタスク実行スクリプト
環境変数から実行タイプとセッション名を取得
"""
import os
import sys
import boto3
from datetime import datetime
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# プロジェクトルートに移動
sys.path.insert(0, '/app')

def main():
    """ECSタスクのメイン処理"""
    try:
        # 実行タイプとセッション名を環境変数から取得
        execution_type = os.environ.get('EXECUTION_TYPE', 'full')
        session_name = os.environ.get('SESSION_NAME', 'アジアセッション')
        
        logger.info(f"=== FX分析実行開始 ===")
        logger.info(f"実行タイプ: {execution_type}")
        logger.info(f"セッション: {session_name}")
        logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # モジュールインポート
        from src.chart_generator import ChartGenerator
        from src.claude_analyzer import ClaudeAnalyzer
        from src.notion_writer import NotionWriter
        from src.notion_analyzer import NotionAnalyzer
        from src.blog_publisher import BlogPublisher
        
        # S3クライアント
        s3_client = boto3.client('s3')
        s3_bucket = os.environ.get('S3_BUCKET', 'fx-analysis-charts')
        
        # 1. チャート生成
        logger.info("チャート生成中...")
        generator = ChartGenerator('USDJPY=X')
        output_dir = Path('/tmp/screenshots') / f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        screenshots = generator.generate_multiple_charts(
            timeframes=['5min', '1hour'],
            output_dir=output_dir,
            candle_count=288
        )
        logger.info(f"チャート生成完了: {output_dir}")
        
        # S3にアップロード
        s3_screenshots = {}
        for timeframe, local_path in screenshots.items():
            s3_key = f"charts/{datetime.now().strftime('%Y/%m/%d')}/{timeframe}_{datetime.now().strftime('%H%M%S')}.png"
            s3_client.upload_file(str(local_path), s3_bucket, s3_key)
            s3_screenshots[timeframe] = f"s3://{s3_bucket}/{s3_key}"
            logger.info(f"S3アップロード: {s3_key}")
        
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
        
        # 4. ブログとX投稿（fullタイプの場合のみ）
        if execution_type == 'full':
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
                
                if results.get('twitter_url'):
                    logger.info(f"X投稿成功: {results['twitter_url']}")
        
        # 5. Slack通知
        logger.info("Slack通知送信中...")
        import requests
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook_url:
            message = {
                "text": f"*FX分析完了 ({session_name})*\n"
                       f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                       f"実行タイプ: {execution_type}\n"
                       f"S3: {s3_bucket}"
            }
            requests.post(webhook_url, json=message)
            logger.info("Slack通知送信完了")
        
        logger.info("=== FX分析実行完了 ===")
        
    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # エラー通知
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook_url:
            import requests
            message = {
                "text": f"*⚠️ FX分析エラー*\n"
                       f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                       f"エラー: {str(e)}"
            }
            requests.post(webhook_url, json=message)
        
        sys.exit(1)

if __name__ == "__main__":
    main()