#!/usr/bin/env python3
"""
直接出力テスト
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 出力先テスト開始 ===")
print(f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数を読み込み
print("\n1. 環境変数読み込み:")

# .env
if os.path.exists('.env'):
    exec(open('.env').read().replace('export ', '').replace('\n', '\nos.environ["').replace('=', '"] = "').replace('"" = ""', '').replace('os.environ["#', '#').replace('os.environ["', ''))
    print("   ✅ .env読み込み")

# .env.phase1
if os.path.exists('.env.phase1'):
    with open('.env.phase1', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print("   ✅ .env.phase1読み込み")

# 2. 簡易チャート生成
print("\n2. チャート生成:")
try:
    from src.chart_generator import ChartGenerator
    generator = ChartGenerator('USDJPY=X')
    output_dir = Path(f"test_output_{datetime.now().strftime('%H%M%S')}")
    output_dir.mkdir(exist_ok=True)
    
    # 5分足のみ生成（時間短縮）
    screenshots = generator.generate_multiple_charts(
        timeframes=['5min'],
        output_dir=output_dir,
        candle_count=100
    )
    print(f"   ✅ チャート生成完了: {list(screenshots.keys())}")
except Exception as e:
    print(f"   ❌ エラー: {e}")
    screenshots = {}

# 3. Slack通知テスト
print("\n3. Slack通知:")
if os.environ.get('ENABLE_PHASE1') == 'true' and os.environ.get('SLACK_WEBHOOK_URL'):
    try:
        import requests
        
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        message = {
            "text": f"🧪 FX分析システム出力テスト\n実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n状態: テスト実行中"
        }
        
        response = requests.post(webhook_url, json=message)
        if response.status_code == 200:
            print("   ✅ Slack通知送信成功")
        else:
            print(f"   ❌ Slack通知失敗: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
else:
    print("   ⚠️ 無効（ENABLE_PHASE1またはSLACK_WEBHOOK_URL未設定）")

# 4. Notion投稿テスト
print("\n4. Notion投稿:")
if os.environ.get('NOTION_API_KEY') and os.environ.get('NOTION_DATABASE_ID'):
    try:
        from src.notion_writer import NotionWriter
        
        writer = NotionWriter()
        test_data = {
            "通貨ペア": "USD/JPY",
            "テスト実行": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "ステータス": "出力テスト"
        }
        
        # シンプルなテストページ作成
        page_id = writer.create_page(
            f"【出力テスト】{datetime.now().strftime('%H:%M')}",
            test_data
        )
        print(f"   ✅ Notionページ作成: {page_id}")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
else:
    print("   ⚠️ 無効（APIキーまたはデータベースID未設定）")

# 5. 設定状態サマリー
print("\n=== 設定状態 ===")
settings = {
    "CLAUDE_API_KEY": "設定済み" if os.environ.get('CLAUDE_API_KEY') else "未設定",
    "NOTION_API_KEY": "設定済み" if os.environ.get('NOTION_API_KEY') else "未設定",
    "SLACK_WEBHOOK_URL": "設定済み" if os.environ.get('SLACK_WEBHOOK_URL') else "未設定",
    "ENABLE_PHASE1": os.environ.get('ENABLE_PHASE1', '未設定'),
    "WORDPRESS_URL": "設定済み" if os.environ.get('WORDPRESS_URL') else "未設定",
    "TWITTER_API_KEY": "設定済み" if os.environ.get('TWITTER_API_KEY') else "未設定"
}

for key, value in settings.items():
    print(f"{key}: {value}")

print("\n✅ テスト完了")