#!/usr/bin/env python3
"""
実際の分析を実行
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# ディレクトリ移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== USD/JPY実分析開始 ===")
print(f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数読み込み
exec(open('.env').read().replace('\n', '\nos.environ["').replace('=', '"] = "').replace('"" = ""', '').replace('os.environ["#', '#').replace('os.environ["', '').replace('export ', ''))

with open('.env.phase1', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher
from src.phase1_alert_system import TradingViewAlertSystem

# 1. チャート生成
print("\n1. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots/real_analysis')
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ 生成完了: {list(screenshots.keys())}")

# 2. 分析
print("\n2. Claude分析...")
analyzer = ClaudeAnalyzer()
analysis = analyzer.analyze_charts(screenshots)
print(f"✅ 分析完了: {len(analysis)}文字")

# 分析結果を保存
with open('real_analysis_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"分析日時: {datetime.now()}\n\n")
    f.write(analysis)

# 3. Slack通知
print("\n3. Slack通知...")
try:
    alert = TradingViewAlertSystem()
    alert.send_slack_alert(
        {'action': 'ANALYSIS', 'entry_price': 0, 'confidence': 0},
        {
            'currency_pair': 'USD/JPY',
            'market_condition': '実分析完了',
            'technical_summary': f"分析時刻: {datetime.now().strftime('%H:%M')}\n{analysis[:300]}..."
        }
    )
    print("✅ 送信完了")
except Exception as e:
    print(f"❌ エラー: {e}")

# 4. Notion投稿
print("\n4. Notion投稿...")
try:
    writer = NotionWriter()
    page_id = writer.create_analysis_page(
        f"USD/JPY実分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        analysis,
        screenshots,
        "USD/JPY"
    )
    print(f"✅ 作成完了: {page_id}")
except Exception as e:
    print(f"❌ エラー: {e}")

# 5. WordPress投稿
print("\n5. WordPress投稿...")
try:
    blog_content = f"""**本記事は投資判断を提供するものではありません。**

{analysis}

---
※教育目的の記事です。投資は自己責任でお願いします。"""

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
        print(f"✅ WordPress: {results['wordpress_url']}")
    if results.get('twitter_url'):
        print(f"✅ Twitter: {results['twitter_url']}")
        
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 実分析投稿完了!")
print("\n確認先:")
print("- Slack: チャンネルを確認")
print("- Notion: データベースを確認")
print("- WordPress: https://by-price-action.com/wp-admin/")
print("- 分析結果: real_analysis_result.txt")