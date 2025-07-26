#!/usr/bin/env python3
"""
FX分析を実行して全プラットフォームに投稿
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== FX分析システム 実行開始 ===")
print(f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数を設定
os.environ.update({
    'CLAUDE_API_KEY': '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',
    'NOTION_API_KEY': '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',
    'NOTION_DATABASE_ID': '21d50adc-70fe-8083-a5a3-e68e8e4464ac',
    'WORDPRESS_URL': 'https://by-price-action.com',
    'WORDPRESS_USERNAME': 'publish',
    'WORDPRESS_PASSWORD': 'aFIxNNhft0lSjkzwI75rYZk2',
    'ENABLE_PHASE1': 'true',
    'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/services/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',
    'FORCE_HOUR': '8',
    'ENABLE_BLOG_POSTING': 'true'
})

# モジュールをインポート
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher
from src.phase1_alert_system import TradingViewAlertSystem

# 1. チャート生成
print("\n1. チャート生成中...")
generator = ChartGenerator('USDJPY=X')
screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=Path('screenshots/post_test'),
    candle_count=288
)
print(f"   ✅ 完了: {len(screenshots)}枚")

# 2. 分析
print("\n2. Claude分析中...")
analyzer = ClaudeAnalyzer()
analysis = analyzer.analyze_charts(screenshots)
print(f"   ✅ 完了: {len(analysis)}文字")

# 3. Slack通知
print("\n3. Slack通知...")
try:
    alert = TradingViewAlertSystem()
    alert.send_slack_alert(
        {'action': 'BUY', 'entry_price': 146.5, 'confidence': 0.8},
        {'currency_pair': 'USD/JPY', 'market_condition': '上昇トレンド', 'technical_summary': analysis[:200]}
    )
    print("   ✅ 送信完了")
except Exception as e:
    print(f"   ❌ エラー: {e}")

# 4. Notion投稿
print("\n4. Notion投稿...")
try:
    writer = NotionWriter()
    page_id = writer.create_analysis_page(
        f"USD/JPY分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        analysis,
        screenshots,
        "USD/JPY"
    )
    print(f"   ✅ 完了: {page_id}")
except Exception as e:
    print(f"   ❌ エラー: {e}")

# 5. WordPress投稿
print("\n5. WordPress投稿...")
try:
    blog_content = f"""**本記事は投資判断を提供するものではありません。**

{analysis}

---
※教育目的の記事です。投資は自己責任でお願いします。"""

    publisher = BlogPublisher(
        {'url': os.environ['WORDPRESS_URL'], 'username': os.environ['WORDPRESS_USERNAME'], 'password': os.environ['WORDPRESS_PASSWORD']},
        {'api_key': '', 'api_secret': '', 'access_token': '', 'access_token_secret': ''}
    )
    
    results = publisher.publish_analysis(blog_content, screenshots)
    
    if results.get('wordpress_url'):
        print(f"   ✅ 完了: {results['wordpress_url']}")
    else:
        print("   ❌ 投稿失敗")
        
except Exception as e:
    print(f"   ❌ エラー: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 実行完了!")
print("\n各プラットフォームで確認してください:")
print("- Slack: チャンネルを確認")
print("- Notion: データベースを確認")
print("- WordPress: https://by-price-action.com/wp-admin/")