#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

# 環境変数を直接読み込み
env_vars = {}
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
                os.environ[key] = value

if os.path.exists('.env.phase1'):
    with open('.env.phase1', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

print("=== WordPress投稿テスト ===")
print(f"URL: {env_vars.get('WORDPRESS_URL')}")
print(f"User: {env_vars.get('WORDPRESS_USERNAME')}")

# 最小限のテスト
from datetime import datetime

# 1. 簡易チャート生成
from src.chart_generator import ChartGenerator
generator = ChartGenerator('USDJPY=X')
screenshots = generator.generate_multiple_charts(
    timeframes=['5min'],
    output_dir='test_charts',
    candle_count=100
)
print(f"チャート生成: {list(screenshots.keys())}")

# 2. テスト投稿
from src.blog_publisher import BlogPublisher

test_content = f"""
**テスト投稿**

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

これはFX分析システムの出力テストです。

WordPress設定が正しく機能しているか確認しています。

---
※テスト投稿
"""

wordpress_config = {
    "url": env_vars.get('WORDPRESS_URL'),
    "username": env_vars.get('WORDPRESS_USERNAME'), 
    "password": env_vars.get('WORDPRESS_PASSWORD')
}

twitter_config = {
    "api_key": env_vars.get('TWITTER_API_KEY'),
    "api_secret": env_vars.get('TWITTER_API_SECRET'),
    "access_token": env_vars.get('TWITTER_ACCESS_TOKEN'),
    "access_token_secret": env_vars.get('TWITTER_ACCESS_TOKEN_SECRET')
}

try:
    publisher = BlogPublisher(wordpress_config, twitter_config)
    
    # デバッグモード有効化
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    results = publisher.publish_analysis(test_content, screenshots)
    
    print("\n結果:")
    print(f"WordPress: {results.get('wordpress_url', '失敗')}")
    print(f"Twitter: {results.get('twitter_url', '失敗')}")
    
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()