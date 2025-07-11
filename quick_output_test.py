#!/usr/bin/env python
"""
クイック出力テスト
"""
import os
import sys
import json
from datetime import datetime

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== FX分析システム 出力確認テスト ===")
print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. 環境変数の確認
print("1. 環境変数の確認:")
env_vars = {
    'NOTION_API_KEY': os.environ.get('NOTION_API_KEY', 'Not set'),
    'NOTION_DATABASE_ID': os.environ.get('NOTION_DATABASE_ID', 'Not set'),
    'SLACK_WEBHOOK_URL': os.environ.get('SLACK_WEBHOOK_URL', 'Not set'),
    'WORDPRESS_URL': os.environ.get('WORDPRESS_URL', 'Not set'),
    'WORDPRESS_USERNAME': os.environ.get('WORDPRESS_USERNAME', 'Not set'),
    'TWITTER_API_KEY': os.environ.get('TWITTER_API_KEY', 'Not set'),
    'ENABLE_PHASE1': os.environ.get('ENABLE_PHASE1', 'Not set')
}

for key, value in env_vars.items():
    if value != 'Not set':
        if 'KEY' in key or 'PASSWORD' in key:
            print(f"   {key}: {value[:8]}...")
        else:
            print(f"   {key}: {value[:30]}...")
    else:
        print(f"   {key}: Not set")

# 2. Phase 1の設定確認
print("\n2. Phase 1の設定確認:")
if os.path.exists('.env.phase1'):
    print("   ✅ .env.phase1が存在します")
    # Phase 1の環境変数を読み込み
    with open('.env.phase1', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    if os.environ.get('ENABLE_PHASE1') == 'true':
        print("   ✅ Phase 1が有効です")
        
        # Slack Webhook確認
        webhook = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook and webhook.startswith('https://hooks.slack.com'):
            print(f"   ✅ Slack Webhook設定済み: {webhook[:40]}...")
        else:
            print("   ❌ Slack Webhookが未設定です")
else:
    print("   ❌ .env.phase1が見つかりません")

# 3. 最新の分析結果を確認
print("\n3. 最新の分析結果:")
if os.path.exists('analysis_summary.json'):
    with open('analysis_summary.json', 'r') as f:
        summary = json.load(f)
    print(f"   タイムスタンプ: {summary.get('timestamp', 'N/A')}")
    print(f"   通貨ペア: {summary.get('currency_pair', 'N/A')}")
    print(f"   推奨: {summary.get('recommendation', 'N/A')}")
else:
    print("   analysis_summary.jsonが見つかりません")

# 4. 出力ログの確認
print("\n4. 各プラットフォームのログ確認:")

# FX分析ログ
if os.path.exists('logs/fx_analysis.log'):
    with open('logs/fx_analysis.log', 'r') as f:
        lines = f.readlines()
        recent = lines[-10:]
        
    notion_output = any('Notion' in line for line in recent)
    blog_output = any('ブログ' in line or 'blog' in line.lower() for line in recent)
    phase1_output = any('Phase 1' in line for line in recent)
    
    print(f"   Notion出力: {'✅' if notion_output else '❌'}")
    print(f"   ブログ出力: {'✅' if blog_output else '❌'}")
    print(f"   Phase 1 (Slack): {'✅' if phase1_output else '❌'}")

# 5. テスト用のSlack通知
print("\n5. テストSlack通知:")
try:
    from src.phase1_alert_system import TradingViewAlertSystem
    
    alert_system = TradingViewAlertSystem()
    test_signal = {
        "action": "TEST",
        "entry_price": 146.50,
        "stop_loss": 146.00,
        "take_profit": 147.00,
        "confidence": 0.99
    }
    
    test_analysis = {
        "timestamp": datetime.now().isoformat(),
        "currency_pair": "USD/JPY",
        "market_condition": "テスト通知",
        "technical_summary": "これは統合テストのための通知です"
    }
    
    # Slack通知を送信
    alert_system.send_slack_alert(test_signal, test_analysis)
    print("   ✅ テストSlack通知を送信しました")
    print("   → Slackチャンネルを確認してください")
    
except Exception as e:
    print(f"   ❌ Slack通知エラー: {e}")

# 6. 出力先の確認方法
print("\n📋 各プラットフォームの確認方法:")
print()
print("1. Slack:")
print("   - 設定したSlackチャンネルを確認")
print("   - 'FX Analysis Alert'というメッセージを探す")
print()
print("2. Notion:")
print("   - 設定したNotionデータベースを確認")
print("   - 最新のページが作成されているか確認")
print()
print("3. ブログ (WordPress):")
print("   - WordPress管理画面にログイン")
print("   - 投稿一覧から最新の記事を確認")
print()
print("4. X (Twitter):")
print("   - analysis_summary.jsonのtwitter_contentを確認")
print("   - 実際の投稿は手動またはAPI経由で実行")

print("\n✅ 出力確認テスト完了！")