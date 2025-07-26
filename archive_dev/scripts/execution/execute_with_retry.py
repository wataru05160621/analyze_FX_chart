#!/usr/bin/env python3
"""
リトライ機能付き実分析実行
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== FX分析システム（リトライ機能付き） ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

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
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher
from src.phase1_alert_system import TradingViewAlertSystem

# 1. チャート生成
print("1. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了: {list(screenshots.keys())}")

# 2. Claude分析（リトライ付き）
print("\n2. Claude分析...")
analyzer = ClaudeAnalyzer()
analysis = None
max_retries = 3
retry_delay = 30  # 30秒待機

for attempt in range(max_retries):
    try:
        print(f"   試行 {attempt + 1}/{max_retries}...")
        analysis = analyzer.analyze_charts(screenshots)
        print(f"   ✅ 分析成功: {len(analysis)}文字")
        break
    except Exception as e:
        if "529" in str(e) or "overloaded" in str(e).lower():
            print(f"   ⚠️ APIオーバーロード。{retry_delay}秒待機...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # 次回は倍の時間待つ
            else:
                print("   ❌ 最大リトライ回数に達しました")
                # デモ分析を使用
                analysis = generate_demo_analysis()
        else:
            print(f"   ❌ エラー: {e}")
            analysis = generate_demo_analysis()
            break

# 分析結果を保存
with open('analysis_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"分析日時: {datetime.now()}\n")
    f.write(f"チャート画像: {output_dir}\n\n")
    f.write(analysis)

# 3. 各プラットフォームへ投稿
print("\n3. 各プラットフォームへ投稿...")

# Slack通知
print("   Slack通知...")
try:
    alert = TradingViewAlertSystem()
    alert.send_slack_alert(
        {'action': 'INFO', 'entry_price': 0, 'confidence': 0},
        {
            'currency_pair': 'USD/JPY',
            'market_condition': 'FX分析完了',
            'technical_summary': f"分析時刻: {datetime.now().strftime('%H:%M')}\n{analysis[:300]}..."
        }
    )
    print("   ✅ Slack送信完了")
except Exception as e:
    print(f"   ❌ Slackエラー: {e}")

# Notion投稿
print("   Notion投稿...")
try:
    writer = NotionWriter()
    page_id = writer.create_analysis_page(
        f"USD/JPY分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        analysis,
        screenshots,
        "USD/JPY"
    )
    print(f"   ✅ Notion投稿完了: {page_id}")
except Exception as e:
    print(f"   ❌ Notionエラー: {e}")

# WordPress投稿
print("   WordPress投稿...")
try:
    blog_content = f"""**本記事は投資判断を提供するものではありません。**FXチャートの分析手法を学習する目的で、現在のチャート状況を解説しています。実際の売買は自己責任で行ってください。

{analysis}

---
※このブログ記事は教育目的で作成されています。投資は自己責任でお願いします。"""

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
    
    # デバッグ情報を有効化
    import logging
    logging.basicConfig(level=logging.INFO)
    
    results = publisher.publish_analysis(blog_content, screenshots)
    
    if results.get('wordpress_url'):
        print(f"   ✅ WordPress投稿: {results['wordpress_url']}")
    else:
        print("   ❌ WordPress投稿失敗")
        
    if results.get('twitter_url'):
        print(f"   ✅ Twitter投稿: {results['twitter_url']}")
    else:
        print("   ℹ️ Twitter投稿はスキップされました")
        
except Exception as e:
    print(f"   ❌ 投稿エラー: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ 処理完了!")
print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n確認先:")
print("- Slack: チャンネルを確認")
print("- Notion: データベースを確認")
print("- WordPress: https://by-price-action.com/wp-admin/")
print(f"- 分析結果: analysis_result.txt")
print(f"- チャート画像: {output_dir}")

def generate_demo_analysis():
    """デモ分析を生成"""
    return f"""# USD/JPY テクニカル分析レポート

分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## 現在の市場状況

USD/JPYは現在、重要な価格帯で推移しています。短期的なトレンドは上昇基調を維持していますが、中期的な視点では横ばいのレンジ相場となっています。

## テクニカル指標の分析

### 移動平均線（EMA）
- 25EMA: 上向き
- 75EMA: 横ばい
- 200EMA: 緩やかな上昇

現在価格は短期移動平均線の上に位置しており、短期的な強気の勢いを示しています。

### サポート・レジスタンス
- 主要レジスタンス: 147.00円
- 主要サポート: 145.50円
- 現在のレンジ: 145.50-147.00円

### トレード戦略

現在の市場環境では、レンジ内でのトレードが有効と考えられます。

**注意事項**
- リスク管理を徹底し、適切なポジションサイズを維持
- 重要な経済指標発表時は注意が必要
- 市場のボラティリティに応じて戦略を調整

※これはAPIオーバーロード時のデモ分析です。実際の市場分析ではありません。"""