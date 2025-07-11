#!/usr/bin/env python3
"""
完全な出力テストを実行
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== FX分析システム 全出力先テスト ===")
print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 環境変数を読み込み
print("1. 環境変数を読み込み中...")

# .env.phase1
if os.path.exists('.env.phase1'):
    with open('.env.phase1', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# .env
if os.path.exists('.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        # dotenvがない場合は手動で読み込み
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value and value not in ['your_value_here', 'your_api_key_here']:
                        os.environ[key] = value

print("   ✅ 環境変数読み込み完了")

# 2. チャート生成（簡易版）
print("\n2. チャート生成:")
try:
    from src.chart_generator import ChartGenerator
    
    generator = ChartGenerator('USDJPY=X')
    output_dir = Path("test_output") / datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 5分足のみ生成（テスト用）
    screenshots = generator.generate_multiple_charts(
        timeframes=['5min'],
        output_dir=output_dir,
        candle_count=100  # 少なめ
    )
    print(f"   ✅ チャート生成成功: {list(screenshots.keys())}")
    
except Exception as e:
    print(f"   ❌ エラー: {e}")
    screenshots = {}

# 3. Slack通知（Phase 1）
print("\n3. Slack通知テスト:")
if os.environ.get('ENABLE_PHASE1') == 'true':
    try:
        from src.phase1_alert_system import TradingViewAlertSystem
        
        alert_system = TradingViewAlertSystem()
        
        # テスト通知
        test_message = f"""
🧪 **FX分析システム 出力テスト**

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
テスト項目:
✅ チャート生成
⏳ Claude分析
⏳ Notion投稿
⏳ WordPress投稿
⏳ X投稿準備

このメッセージが表示されていれば、Slack通知は正常です。
"""
        
        # send_slack_alertメソッドを使用
        alert_system.send_slack_alert(
            signal={"action": "TEST", "confidence": 1.0},
            analysis_summary={
                "currency_pair": "USD/JPY",
                "market_condition": "出力テスト実行中",
                "technical_summary": test_message
            }
        )
        
        print("   ✅ Slack通知送信完了（Slackアプリで確認してください）")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ⚠️ Phase 1が無効です")

# 4. Notion投稿
print("\n4. Notion投稿テスト:")
if os.environ.get('NOTION_API_KEY'):
    try:
        from src.notion_writer import NotionWriter
        
        writer = NotionWriter()
        
        # テスト分析
        test_analysis = f"""
# 出力テスト分析

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## テスト内容
これは全出力先への投稿テストです。

## 確認項目
- チャート生成: ✅
- Slack通知: ✅  
- Notion投稿: 実行中
- WordPress: 未実行
- X: 未実行
"""
        
        page_id = writer.create_analysis_page(
            title=f"【出力テスト】{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            analysis=test_analysis,
            chart_images=screenshots,
            currency="TEST"
        )
        
        print(f"   ✅ Notionページ作成: {page_id}")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ⚠️ Notion APIキーが未設定です")

# 5. WordPress投稿
print("\n5. WordPress投稿テスト:")
wp_url = os.environ.get('WORDPRESS_URL')
wp_user = os.environ.get('WORDPRESS_USERNAME')
wp_pass = os.environ.get('WORDPRESS_PASSWORD')

if all([wp_url, wp_user, wp_pass]):
    try:
        from src.blog_publisher import BlogPublisher
        
        blog_content = f"""
**これは出力テストです**

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FX分析システムの全出力先への投稿テストを実行しています。

## テスト結果
- チャート生成: ✅
- Slack通知: ✅
- Notion投稿: ✅
- WordPress投稿: 実行中

---
※このブログ記事はテスト用です。
"""
        
        wordpress_config = {
            "url": wp_url,
            "username": wp_user,
            "password": wp_pass
        }
        
        # Twitterは設定なしでも動作するように
        twitter_config = {
            "api_key": os.environ.get('TWITTER_API_KEY', 'dummy'),
            "api_secret": os.environ.get('TWITTER_API_SECRET', 'dummy'),
            "access_token": os.environ.get('TWITTER_ACCESS_TOKEN', 'dummy'),
            "access_token_secret": os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', 'dummy')
        }
        
        publisher = BlogPublisher(wordpress_config, twitter_config)
        
        # ログを有効化
        import logging
        logging.basicConfig(level=logging.INFO)
        
        results = publisher.publish_analysis(blog_content, screenshots)
        
        if results.get('wordpress_url'):
            print(f"   ✅ WordPress投稿成功: {results['wordpress_url']}")
        else:
            print("   ❌ WordPress投稿失敗")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ⚠️ WordPress認証情報が未設定です")
    missing = []
    if not wp_url: missing.append("WORDPRESS_URL")
    if not wp_user: missing.append("WORDPRESS_USERNAME")
    if not wp_pass: missing.append("WORDPRESS_PASSWORD")
    print(f"      未設定: {', '.join(missing)}")

# 6. 結果サマリー
print("\n" + "="*50)
print("📊 最終結果")
print("="*50)

# ログファイルの最新エントリを確認
if os.path.exists('logs/fx_analysis.log'):
    with open('logs/fx_analysis.log', 'r') as f:
        lines = f.readlines()
        recent_lines = lines[-20:]
        
        print("\n最近のログ:")
        for line in recent_lines:
            if any(word in line for word in ['Slack', 'Notion', 'WordPress', 'ERROR']):
                print(f"  {line.strip()}")

print(f"\n✅ テスト完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n次の場所で結果を確認してください:")
print("- Slack: 設定したチャンネル")
print("- Notion: データベースページ")
print("- WordPress: 管理画面の投稿一覧")
print("- ログ: logs/fx_analysis.log")