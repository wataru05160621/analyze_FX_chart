#!/usr/bin/env python3
"""
全プラットフォームへの完全投稿スクリプト
Notion、WordPress、X (Twitter)、Slackへ同時投稿
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== 全プラットフォーム投稿実行 ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("投稿先: Notion, WordPress, X (Twitter), Slack")

# 環境変数読み込み
print("\n1. 環境変数読み込み...")
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            if '#' in line:
                line = line.split('#')[0].strip()
            key, value = line.strip().split('=', 1)
            if value and value not in ['your_value_here', 'your_api_key_here']:
                os.environ[key] = value

with open('.env.phase1', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# APIキー確認
api_key = os.environ.get('CLAUDE_API_KEY')
if not api_key:
    print("❌ CLAUDE_API_KEYが見つかりません")
    sys.exit(1)

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher
from src.phase1_notification import Phase1NotificationSystem

# ログ設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 2. チャート生成
print("\n2. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")
for tf, path in screenshots.items():
    print(f"   {tf}: {path}")

# 3. Claude分析（Volmanメソッド）
print("\n3. Claude分析実行...")
analyzer = ClaudeAnalyzer()

try:
    analysis = analyzer.analyze_charts(screenshots)
    print(f"✅ 分析完了: {len(analysis)}文字")
    
    # 分析結果を保存
    analysis_file = 'latest_complete_analysis.txt'
    with open(analysis_file, 'w', encoding='utf-8') as f:
        f.write(f"分析日時: {datetime.now()}\n")
        f.write(f"チャート画像: {output_dir}\n\n")
        f.write(analysis)
    print(f"✅ 分析結果保存: {analysis_file}")
    
except Exception as e:
    print(f"❌ 分析エラー: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 全プラットフォームへの投稿
print("\n4. 全プラットフォームへの投稿開始...")

# 投稿結果を記録
posting_results = {
    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'chart_dir': str(output_dir),
    'platforms': {}
}

# 4.1 Slack投稿
print("\n[1/4] Slack投稿...")
try:
    notification = Phase1NotificationSystem()
    notification.send_completion_notification(
        "USD/JPY",
        {
            'analysis': analysis,
            'chart_paths': screenshots
        }
    )
    posting_results['platforms']['slack'] = {'status': 'success', 'message': 'Slack通知送信完了'}
    print("✅ Slack投稿成功")
except Exception as e:
    posting_results['platforms']['slack'] = {'status': 'failed', 'error': str(e)}
    print(f"❌ Slackエラー: {e}")
    # 直接Webhook送信を試みる
    try:
        import requests
        webhook = os.environ.get('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/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')
        
        # 分析の要約
        summary = analysis[:500] if len(analysis) > 500 else analysis
        message = {
            "text": f"*FX分析完了 (Volmanメソッド)*\n"
                   f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                   f"通貨ペア: USD/JPY\n\n"
                   f"{summary}..."
        }
        
        resp = requests.post(webhook, json=message)
        if resp.status_code == 200:
            posting_results['platforms']['slack'] = {'status': 'success', 'message': 'Webhook送信成功'}
            print("✅ Slack投稿成功（Webhook直接送信）")
    except Exception as webhook_error:
        print(f"   Webhookエラー: {webhook_error}")

# 4.2 Notion投稿（詳細版）
print("\n[2/4] Notion投稿...")
try:
    # Notion用の詳細分析を生成
    from src.notion_analyzer import NotionAnalyzer
    notion_analyzer = NotionAnalyzer()
    detailed_analysis = notion_analyzer.create_detailed_analysis(analysis)
    
    writer = NotionWriter()
    page_id = writer.create_analysis_page(
        f"USD/JPY分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        detailed_analysis,  # 詳細版を使用
        screenshots,
        "USD/JPY"
    )
    posting_results['platforms']['notion'] = {
        'status': 'success',
        'page_id': page_id,
        'url': f"https://notion.so/{page_id.replace('-', '')}"
    }
    print(f"✅ Notion投稿成功: {page_id}")
    print("   （環境認識・ビルドアップ・ダマシ分析含む詳細版）")
except Exception as e:
    posting_results['platforms']['notion'] = {'status': 'failed', 'error': str(e)}
    print(f"❌ Notionエラー: {e}")

# 4.3 WordPress + X (Twitter) 投稿
print("\n[3/4] WordPress投稿...")
try:
    # ブログ用コンテンツ
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
        posting_results['platforms']['wordpress'] = {
            'status': 'success',
            'url': results['wordpress_url']
        }
        print(f"✅ WordPress投稿成功: {results['wordpress_url']}")
        
        # 4.4 X (Twitter) 投稿
        print("\n[4/4] X (Twitter)投稿...")
        if results.get('twitter_url'):
            posting_results['platforms']['twitter'] = {
                'status': 'success',
                'url': results['twitter_url']
            }
            print(f"✅ X投稿成功: {results['twitter_url']}")
        else:
            # 手動でTwitter投稿を試みる
            try:
                twitter_url = publisher.publish_to_twitter(analysis, results['wordpress_url'])
                if twitter_url:
                    posting_results['platforms']['twitter'] = {
                        'status': 'success',
                        'url': twitter_url
                    }
                    print(f"✅ X投稿成功: {twitter_url}")
                else:
                    posting_results['platforms']['twitter'] = {
                        'status': 'failed',
                        'error': 'Twitter投稿が返されませんでした'
                    }
                    print("❌ X投稿失敗")
            except Exception as tw_error:
                posting_results['platforms']['twitter'] = {
                    'status': 'failed',
                    'error': str(tw_error)
                }
                print(f"❌ Xエラー: {tw_error}")
    else:
        posting_results['platforms']['wordpress'] = {
            'status': 'failed',
            'error': 'WordPress投稿が失敗しました'
        }
        posting_results['platforms']['twitter'] = {
            'status': 'skipped',
            'reason': 'WordPress投稿が失敗したため'
        }
        print("❌ WordPress投稿失敗")
        
except Exception as e:
    posting_results['platforms']['wordpress'] = {'status': 'failed', 'error': str(e)}
    posting_results['platforms']['twitter'] = {'status': 'failed', 'error': str(e)}
    print(f"❌ 投稿エラー: {e}")
    import traceback
    traceback.print_exc()

# 5. 投稿結果サマリー
print("\n=== 投稿結果サマリー ===")
print(f"実行時刻: {posting_results['analysis_time']}")
print(f"チャート: {posting_results['chart_dir']}")
print("\n投稿状況:")

success_count = 0
for platform, result in posting_results['platforms'].items():
    status_icon = "✅" if result['status'] == 'success' else "❌"
    print(f"{status_icon} {platform.upper()}: {result['status']}")
    if result['status'] == 'success':
        success_count += 1
        if 'url' in result:
            print(f"   URL: {result['url']}")
        if 'page_id' in result:
            print(f"   Page ID: {result['page_id']}")
    elif result['status'] == 'failed':
        print(f"   エラー: {result.get('error', 'Unknown error')}")

# 結果をJSONファイルに保存
import json
with open('posting_results.json', 'w', encoding='utf-8') as f:
    json.dump(posting_results, f, ensure_ascii=False, indent=2)

print(f"\n投稿成功: {success_count}/4 プラットフォーム")
print("詳細な結果: posting_results.json")

# 6. 確認方法
print("\n=== 各プラットフォームでの確認方法 ===")
print("1. Slack: 設定したチャンネルを確認")
print("2. Notion: https://notion.so のデータベースを確認")
print("3. WordPress: https://by-price-action.com/wp-admin/ の投稿一覧")
print("4. X (Twitter): アカウントのタイムラインを確認")

print("\n✅ 全投稿処理完了!")

# エラーがあった場合は終了コード1で終了
if success_count < 4:
    sys.exit(1)