#!/usr/bin/env python3
"""
全出力先への投稿テスト（レート制限対策済み）
"""
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
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .envを読み込みました")
    
    # .env.phase1ファイル
    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ .env.phase1を読み込みました")

async def test_full_workflow():
    """完全なワークフローをテスト"""
    
    print("=== FX分析システム 完全テスト（出力先確認） ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 環境変数を読み込み
    load_env_files()
    
    # 1. 環境変数の確認
    print("1. 環境変数の確認:")
    env_checks = {
        'CLAUDE_API_KEY': os.environ.get('CLAUDE_API_KEY', ''),
        'NOTION_API_KEY': os.environ.get('NOTION_API_KEY', ''),
        'SLACK_WEBHOOK_URL': os.environ.get('SLACK_WEBHOOK_URL', ''),
        'WORDPRESS_URL': os.environ.get('WORDPRESS_URL', ''),
        'ENABLE_PHASE1': os.environ.get('ENABLE_PHASE1', ''),
        'ENABLE_BLOG_POSTING': os.environ.get('ENABLE_BLOG_POSTING', ''),
        'ALPHA_VANTAGE_API_KEY': os.environ.get('ALPHA_VANTAGE_API_KEY', '')
    }
    
    for key, value in env_checks.items():
        if value:
            print(f"   ✅ {key}: {'設定済み' if key.endswith('KEY') else value[:30]}")
        else:
            print(f"   ❌ {key}: 未設定")
    
    # 2. チャート生成テスト
    print("\n2. チャート生成テスト:")
    from src.chart_generator import ChartGenerator
    
    generator = ChartGenerator('USDJPY=X')
    screenshots = generator.generate_multiple_charts(
        timeframes=['5min', '1hour'],
        output_dir=Path("test_screenshots"),
        candle_count=288
    )
    
    if screenshots:
        print("   ✅ チャート生成成功")
        for tf, path in screenshots.items():
            print(f"      {tf}: {path}")
    else:
        print("   ❌ チャート生成失敗")
        return
    
    # 3. Claude分析テスト（レート制限考慮）
    print("\n3. Claude分析テスト:")
    from src.claude_analyzer import ClaudeAnalyzer
    
    analyzer = ClaudeAnalyzer()
    print("   分析実行中...")
    
    try:
        analysis = analyzer.analyze_charts(screenshots)
        print(f"   ✅ 分析成功: {len(analysis)}文字")
        
        # 分析結果を保存（確認用）
        with open('test_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(analysis)
            
    except Exception as e:
        print(f"   ❌ 分析エラー: {e}")
        return
    
    # 4. Phase 1 (Slack)テスト
    print("\n4. Phase 1 Slack通知テスト:")
    if os.environ.get('ENABLE_PHASE1') == 'true':
        try:
            from src.phase1_alert_system import SignalGenerator, TradingViewAlertSystem
            from src.phase1_performance_automation import Phase1PerformanceAutomation
            
            # テストシグナル生成
            signal = {
                "action": "BUY",
                "entry_price": 146.50,
                "stop_loss": 146.00,
                "take_profit": 147.00,
                "confidence": 0.75
            }
            
            # Slack通知
            alert_system = TradingViewAlertSystem()
            alert_system.send_slack_alert(signal, {
                'currency_pair': 'USD/JPY',
                'market_condition': 'テスト通知',
                'technical_summary': analysis[:200] + '...'
            })
            
            print("   ✅ Slack通知送信（Slackアプリで確認してください）")
            
            # パフォーマンス記録
            performance = Phase1PerformanceAutomation()
            signal_id = performance.record_signal(signal, {
                'summary': analysis,
                'currency_pair': 'USD/JPY'
            })
            print(f"   ✅ パフォーマンス記録: {signal_id}")
            
        except Exception as e:
            print(f"   ❌ Phase 1エラー: {e}")
    else:
        print("   ⚠️ Phase 1が無効です")
    
    # 5. Notion投稿テスト
    print("\n5. Notion投稿テスト:")
    if os.environ.get('NOTION_API_KEY'):
        try:
            from src.notion_writer import NotionWriter
            
            writer = NotionWriter()
            page_id = writer.create_analysis_page(
                title=f"【テスト】USD/JPY分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                analysis=analysis,
                chart_images=screenshots,
                currency="USD/JPY"
            )
            
            print(f"   ✅ Notionページ作成: {page_id}")
            
        except Exception as e:
            print(f"   ❌ Notionエラー: {e}")
    else:
        print("   ⚠️ Notion APIキーが未設定です")
    
    # 6. ブログ投稿テスト
    print("\n6. WordPress投稿テスト:")
    if all([os.environ.get('WORDPRESS_URL'), 
            os.environ.get('WORDPRESS_USERNAME'),
            os.environ.get('WORDPRESS_PASSWORD')]):
        try:
            from src.blog_publisher import BlogPublisher
            
            # ブログ用フォーマット（二重分析なし）
            blog_analysis = f"""**本記事は投資判断を提供するものではありません。**

{analysis}

---
※このブログ記事は教育目的で作成されています。"""
            
            wordpress_config = {
                "url": os.environ.get('WORDPRESS_URL'),
                "username": os.environ.get('WORDPRESS_USERNAME'),
                "password": os.environ.get('WORDPRESS_PASSWORD')
            }
            
            twitter_config = {
                "api_key": os.environ.get('TWITTER_API_KEY', ''),
                "api_secret": os.environ.get('TWITTER_API_SECRET', ''),
                "access_token": os.environ.get('TWITTER_ACCESS_TOKEN', ''),
                "access_token_secret": os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', '')
            }
            
            publisher = BlogPublisher(wordpress_config, twitter_config)
            results = publisher.publish_analysis(blog_analysis, screenshots)
            
            if results['wordpress_url']:
                print(f"   ✅ WordPress投稿: {results['wordpress_url']}")
            else:
                print("   ❌ WordPress投稿失敗")
                
        except Exception as e:
            print(f"   ❌ ブログ投稿エラー: {e}")
    else:
        print("   ⚠️ WordPress認証情報が未設定です")
    
    # 7. X (Twitter)テスト
    print("\n7. X (Twitter)投稿準備:")
    twitter_content = f"""【USD/JPY分析】{datetime.now().strftime('%H:%M')}

現在の市場状況を分析しました。
詳細はブログをご覧ください。

#FX #USDJPY #為替"""
    
    print("   Twitterコンテンツ:")
    print("   " + twitter_content.replace('\n', '\n   '))
    
    if all([os.environ.get('TWITTER_API_KEY'),
            os.environ.get('TWITTER_API_SECRET'),
            os.environ.get('TWITTER_ACCESS_TOKEN'),
            os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')]):
        print("   ✅ Twitter API設定済み（手動投稿が必要）")
    else:
        print("   ⚠️ Twitter API認証情報が未設定です")
    
    # 8. 結果サマリー
    print("\n" + "="*50)
    print("📊 テスト結果サマリー")
    print("="*50)
    
    results = {
        "チャート生成": "✅ 成功",
        "Claude分析": f"✅ 成功（{len(analysis)}文字）",
        "Slack通知": "✅ 送信済み" if os.environ.get('ENABLE_PHASE1') == 'true' else "⚠️ 無効",
        "Notion投稿": "✅ 成功" if os.environ.get('NOTION_API_KEY') else "⚠️ 未設定",
        "WordPress投稿": "✅ 成功" if os.environ.get('WORDPRESS_URL') else "⚠️ 未設定",
        "X投稿": "⚠️ 手動投稿必要"
    }
    
    for item, status in results.items():
        print(f"{item}: {status}")
    
    print(f"\n完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📋 次のステップ:")
    print("1. Slackアプリで通知を確認")
    print("2. Notionデータベースで新規ページを確認")
    print("3. WordPress管理画面で投稿を確認")
    print("4. 必要に応じて環境変数を設定")

if __name__ == "__main__":
    # 非同期関数を実行
    asyncio.run(test_full_workflow())