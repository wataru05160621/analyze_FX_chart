#!/usr/bin/env python3
"""
全出力先への投稿テストを実行
"""
import subprocess
import sys
import os
from datetime import datetime

print("=== FX分析システム 全出力先テスト ===")
print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 環境変数を設定
env = os.environ.copy()
env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
env['TEST_MODE'] = 'true'  # テストモード

# Pythonスクリプトを直接実行
script_content = '''
import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境変数を読み込み
def load_env_files():
    """すべての環境変数ファイルを読み込み"""
    # .envファイル
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 値が空でない場合のみ設定
                    if value and value not in ['your_value_here', 'your_api_key_here']:
                        os.environ[key] = value
    
    # .env.phase1ファイル
    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value:
                        os.environ[key] = value
    
    print("環境変数を読み込みました")

# 環境変数を読み込み
load_env_files()

# 各モジュールをインポート
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter

print("\\n1. チャート生成テスト:")
try:
    generator = ChartGenerator('USDJPY=X')
    screenshots = generator.generate_multiple_charts(
        timeframes=['5min', '1hour'],
        output_dir=Path("test_output_" + datetime.now().strftime('%Y%m%d_%H%M%S')),
        candle_count=288
    )
    print(f"   ✅ チャート生成成功: {len(screenshots)}枚")
    for tf, path in screenshots.items():
        print(f"      {tf}: {path.name}")
except Exception as e:
    print(f"   ❌ エラー: {e}")
    screenshots = None

if screenshots:
    print("\\n2. Claude分析テスト:")
    try:
        analyzer = ClaudeAnalyzer()
        analysis = analyzer.analyze_charts(screenshots)
        print(f"   ✅ 分析成功: {len(analysis)}文字")
        
        # テスト用の短縮版
        test_analysis = analysis[:1000] + "\\n\\n[テスト用に短縮]"
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        test_analysis = "テスト分析結果"
else:
    test_analysis = "テスト分析結果（チャート生成エラーのため仮データ）"

# 3. Slack通知テスト（Phase 1）
print("\\n3. Slack通知テスト:")
if os.environ.get('ENABLE_PHASE1') == 'true':
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
        
        alert_system.send_slack_alert(test_signal, {
            'currency_pair': 'USD/JPY',
            'market_condition': '全出力先テスト実行中',
            'technical_summary': f'テスト実行時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        })
        print("   ✅ Slack通知送信完了")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
else:
    print("   ⚠️ Phase 1が無効です（ENABLE_PHASE1=true に設定してください）")

# 4. Notion投稿テスト
print("\\n4. Notion投稿テスト:")
if os.environ.get('NOTION_API_KEY'):
    try:
        writer = NotionWriter()
        page_id = writer.create_analysis_page(
            title=f"【テスト】全出力先確認 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            analysis=test_analysis,
            chart_images=screenshots if screenshots else {},
            currency="USD/JPY"
        )
        print(f"   ✅ Notionページ作成: {page_id}")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
else:
    print("   ⚠️ Notion APIキーが未設定です")

# 5. WordPress投稿テスト
print("\\n5. WordPress投稿テスト:")
wp_url = os.environ.get('WORDPRESS_URL')
wp_user = os.environ.get('WORDPRESS_USERNAME')
wp_pass = os.environ.get('WORDPRESS_PASSWORD')

if all([wp_url, wp_user, wp_pass]):
    try:
        from src.blog_publisher import BlogPublisher
        
        blog_content = f"""**テスト投稿です**

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{test_analysis}

---
※これは出力テスト用の投稿です。"""
        
        wordpress_config = {
            "url": wp_url,
            "username": wp_user,
            "password": wp_pass
        }
        
        twitter_config = {
            "api_key": os.environ.get('TWITTER_API_KEY', ''),
            "api_secret": os.environ.get('TWITTER_API_SECRET', ''),
            "access_token": os.environ.get('TWITTER_ACCESS_TOKEN', ''),
            "access_token_secret": os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', '')
        }
        
        publisher = BlogPublisher(wordpress_config, twitter_config)
        
        # デバッグ情報を有効化
        import logging
        logging.basicConfig(level=logging.INFO)
        
        results = publisher.publish_analysis(blog_content, screenshots if screenshots else {})
        
        if results['wordpress_url']:
            print(f"   ✅ WordPress投稿成功: {results['wordpress_url']}")
        else:
            print("   ❌ WordPress投稿失敗")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ⚠️ WordPress認証情報が未設定です")
    print(f"      WORDPRESS_URL: {'設定済み' if wp_url else '未設定'}")
    print(f"      WORDPRESS_USERNAME: {'設定済み' if wp_user else '未設定'}")
    print(f"      WORDPRESS_PASSWORD: {'設定済み' if wp_pass else '未設定'}")

# 6. X (Twitter)コンテンツ生成
print("\\n6. X (Twitter)コンテンツ生成:")
twitter_content = f"""【テスト投稿】{datetime.now().strftime('%H:%M')}

FX分析システムの出力テストを実行中です。
全ての出力先への投稿を確認しています。

#FXテスト #システムテスト"""

print("   生成されたコンテンツ:")
print("   " + twitter_content.replace('\\n', '\\n   '))

if all([os.environ.get('TWITTER_API_KEY'),
        os.environ.get('TWITTER_API_SECRET'),
        os.environ.get('TWITTER_ACCESS_TOKEN'),
        os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')]):
    print("   ✅ Twitter API設定済み")
else:
    print("   ⚠️ Twitter API認証情報が未設定です")

# 7. 結果サマリー
print("\\n" + "="*50)
print("📊 テスト結果サマリー")
print("="*50)

# 各種設定状態を確認
checks = {
    "Claude API": bool(os.environ.get('CLAUDE_API_KEY')),
    "Notion API": bool(os.environ.get('NOTION_API_KEY')),
    "Slack Webhook": bool(os.environ.get('SLACK_WEBHOOK_URL')) and os.environ.get('ENABLE_PHASE1') == 'true',
    "WordPress": all([wp_url, wp_user, wp_pass]),
    "Twitter API": all([os.environ.get('TWITTER_API_KEY'),
                       os.environ.get('TWITTER_API_SECRET'),
                       os.environ.get('TWITTER_ACCESS_TOKEN'),
                       os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')])
}

for item, status in checks.items():
    print(f"{item}: {'✅ 設定済み' if status else '❌ 未設定'}")

print(f"\\n完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
'''

# Pythonコードを実行
try:
    result = subprocess.run(
        [sys.executable, '-c', script_content],
        env=env,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print(result.stdout)
    
    if result.stderr:
        print("\nエラー出力:")
        print(result.stderr)
        
except Exception as e:
    print(f"実行エラー: {e}")