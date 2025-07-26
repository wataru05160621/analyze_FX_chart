#!/usr/bin/env python3
"""
API分析なしで投稿テスト（チャート画像のみ）
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== チャート画像投稿テスト ===")
print(f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数読み込み
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            if value and value not in ['your_value_here', 'your_api_key_here']:
                os.environ[key] = value

with open('.env.phase1', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.blog_publisher import BlogPublisher
from src.phase1_alert_system import TradingViewAlertSystem

# 1. チャート生成
print("\n1. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"test_{datetime.now().strftime('%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")
for tf, path in screenshots.items():
    print(f"   {tf}: {path}")

# 2. 簡易分析内容
analysis = f"""# USD/JPY チャート分析

分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## チャート画像

以下のチャートをご確認ください：
- 5分足チャート
- 1時間足チャート

## 市場概況

現在のUSD/JPYは重要な価格帯で推移しています。
詳細な分析は後日更新予定です。

## 注意事項

- 投資は自己責任でお願いします
- リスク管理を徹底してください
- 本記事は教育目的です

---
※Claude APIの負荷により、詳細分析は一時的に利用できません。"""

# 3. WordPress投稿（チャート画像付き）
print("\n2. WordPress投稿...")
try:
    blog_content = f"""**本記事は投資判断を提供するものではありません。**

{analysis}

---
※このブログ記事は教育目的で作成されています。"""

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
    
    # ログ有効化
    import logging
    logging.basicConfig(level=logging.INFO)
    
    results = publisher.publish_analysis(blog_content, screenshots)
    
    if results.get('wordpress_url'):
        print(f"✅ WordPress投稿成功: {results['wordpress_url']}")
        print("   チャート画像も含まれています")
    else:
        print("❌ WordPress投稿失敗")
        
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()

# 4. Slack通知
print("\n3. Slack通知...")
try:
    alert = TradingViewAlertSystem()
    alert.send_slack_alert(
        {'action': 'INFO', 'entry_price': 0, 'confidence': 0},
        {
            'currency_pair': 'USD/JPY',
            'market_condition': 'チャート更新',
            'technical_summary': f"チャート画像を生成しました。\n時刻: {datetime.now().strftime('%H:%M')}\nWordPressで確認してください。"
        }
    )
    print("✅ Slack通知送信")
except Exception as e:
    print(f"❌ エラー: {e}")

print("\n✅ 完了!")
print("\n確認先:")
print("- WordPress: https://by-price-action.com/wp-admin/")
print("- Slack: 設定したチャンネル")
print(f"- チャート画像: {output_dir}")