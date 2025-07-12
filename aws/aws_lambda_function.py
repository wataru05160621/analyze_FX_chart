"""
AWS Lambda function for FX analysis
検証日数機能付き
"""
import os
import sys
import json
import logging
from datetime import datetime
import pytz

# Lambda環境のパス設定
sys.path.insert(0, '/opt/python')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# タイムゾーン設定
JST = pytz.timezone('Asia/Tokyo')

def lambda_handler(event, context):
    """Lambda function handler"""
    try:
        # 実行時間を取得
        current_hour = datetime.now(JST).hour
        is_full_posting = current_hour == 8  # 8時は全プラットフォーム投稿
        
        # 検証日数を取得
        from src.verification_tracker_s3 import get_tracker
        tracker = get_tracker()
        verification_day = tracker.get_verification_text()
        phase_info = tracker.get_phase_info()
        
        logger.info(f"Lambda実行開始: {datetime.now(JST).strftime('%Y-%m-%d %H:%M')} JST - {verification_day}")
        logger.info(f"フェーズ: {phase_info['current_phase']} - {phase_info['description']}")
        logger.info(f"投稿モード: {'全プラットフォーム' if is_full_posting else 'Notionのみ'}")
        
        # 環境変数から認証情報を読み込み
        load_secrets()
        
        # 分析実行
        from src.s3_chart_fetcher import S3ChartFetcher
        from src.claude_analyzer import ClaudeAnalyzer
        
        # S3からチャート取得
        logger.info("S3からチャート取得中...")
        chart_fetcher = S3ChartFetcher()
        chart_data = chart_fetcher.fetch_latest_charts(
            symbol="USDJPY",
            timeframes=['5min', '1hour', '4hour', '1day']
        )
        
        if not chart_data:
            logger.error("チャート画像が取得できませんでした")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'No charts available',
                    'message': 'Failed to fetch charts from S3'
                })
            }
        
        # チャートパスの辞書を作成（Pathオブジェクトとして）
        from pathlib import Path
        screenshots = {}
        for chart in chart_data:
            screenshots[chart['timeframe']] = Path(chart['path'])
        
        # Claude分析
        logger.info("Claude分析実行中...")
        analyzer = ClaudeAnalyzer()
        analysis = analyzer.analyze_charts(screenshots)
        
        # 投稿処理
        results = {}
        
        # Notion投稿（常に実行）
        logger.info("Notion投稿中...")
        from src.notion_writer import NotionWriter
        writer = NotionWriter()
        page_id = writer.create_analysis_page(
            f"USD/JPY分析 {datetime.now(JST).strftime('%Y-%m-%d %H:%M')} - {verification_day}",
            analysis,
            screenshots,
            "USD/JPY"
        )
        results['notion'] = {'status': 'success', 'page_id': page_id}
        
        if is_full_posting:
            # WordPress投稿
            logger.info("WordPress/X投稿中...")
            from src.blog_publisher import BlogPublisher
            
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
            pub_results = publisher.publish_analysis(analysis, screenshots)
            results['wordpress'] = pub_results.get('wordpress_url')
            results['twitter'] = pub_results.get('twitter_url')
            
            # Slack通知
            logger.info("Slack通知送信中...")
            send_slack_notification(analysis, results, verification_day)
        
        # 結果を返す
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analysis completed successfully',
                'verification_day': verification_day,
                'phase': phase_info['current_phase'],
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # エラー通知
        try:
            send_error_notification(str(e))
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Analysis failed'
            })
        }

def load_secrets():
    """AWS Secrets Managerから認証情報を読み込み"""
    import boto3
    
    secrets_client = boto3.client('secretsmanager')
    
    # Claude API Key
    try:
        response = secrets_client.get_secret_value(SecretId='fx-analysis/claude-api-key')
        secret = json.loads(response['SecretString'])
        os.environ['CLAUDE_API_KEY'] = secret['api_key']
    except Exception as e:
        logger.error(f"Claude API Key取得エラー: {e}")
    
    # WordPress credentials
    try:
        response = secrets_client.get_secret_value(SecretId='fx-analysis/wordpress-credentials')
        secret = json.loads(response['SecretString'])
        os.environ['WORDPRESS_URL'] = secret['url']
        os.environ['WORDPRESS_USERNAME'] = secret['username']
        os.environ['WORDPRESS_PASSWORD'] = secret['password']
    except Exception as e:
        logger.error(f"WordPress credentials取得エラー: {e}")
    
    # その他の環境変数はLambda環境変数から取得

def send_slack_notification(analysis, results, verification_day):
    """Slack通知を送信"""
    import requests
    
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    
    # 分析サマリー
    summary = analysis[:500] + "..." if len(analysis) > 500 else analysis
    
    message = {
        "text": f"*FX分析完了 (Volmanメソッド) - {verification_day}*",
        "attachments": [
            {
                "color": "good",
                "fields": [
                    {
                        "title": "実行時刻",
                        "value": datetime.now(JST).strftime('%Y-%m-%d %H:%M'),
                        "short": True
                    },
                    {
                        "title": "通貨ペア",
                        "value": "USD/JPY",
                        "short": True
                    },
                    {
                        "title": "投稿結果",
                        "value": f"Notion: ✅\nWordPress: {'✅' if results.get('wordpress') else '❌'}\nX: {'✅' if results.get('twitter') else '❌'}",
                        "short": True
                    }
                ],
                "text": summary
            }
        ]
    }
    
    response = requests.post(webhook_url, json=message)
    if response.status_code != 200:
        logger.error(f"Slack通知エラー: {response.status_code}")

def send_error_notification(error_message):
    """エラー通知を送信"""
    import requests
    
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    
    message = {
        "text": "*⚠️ FX分析エラー*",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {
                        "title": "エラー時刻",
                        "value": datetime.now(JST).strftime('%Y-%m-%d %H:%M'),
                        "short": True
                    },
                    {
                        "title": "エラー内容",
                        "value": error_message[:200],
                        "short": False
                    }
                ]
            }
        ]
    }
    
    requests.post(webhook_url, json=message)