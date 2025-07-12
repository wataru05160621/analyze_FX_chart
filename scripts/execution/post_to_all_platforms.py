#!/usr/bin/env python3
"""
全プラットフォームへ実際に投稿
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境変数を読み込み
def load_env_files():
    """環境変数ファイルを読み込み"""
    # .env
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value and value not in ['your_value_here', 'your_api_key_here']:
                        os.environ[key] = value
    
    # .env.phase1
    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

async def post_to_all():
    """全プラットフォームへ投稿"""
    
    print("=== FX分析システム 全プラットフォーム投稿 ===")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 環境変数を読み込み
    load_env_files()
    
    # 1. チャート生成
    print("1. チャート生成:")
    from src.chart_generator import ChartGenerator
    
    try:
        generator = ChartGenerator('USDJPY=X')
        output_dir = Path("screenshots") / "test_post"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        screenshots = generator.generate_multiple_charts(
            timeframes=['5min', '1hour'],
            output_dir=output_dir,
            candle_count=288
        )
        print(f"   ✅ チャート生成成功: {len(screenshots)}枚")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return
    
    # 2. Claude分析
    print("\n2. Claude分析:")
    from src.claude_analyzer import ClaudeAnalyzer
    
    try:
        analyzer = ClaudeAnalyzer()
        analysis_result = analyzer.analyze_charts(screenshots)
        print(f"   ✅ 分析完了: {len(analysis_result)}文字")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        # テスト用の分析結果
        analysis_result = f"""
# USD/JPY 分析レポート

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 現在の相場状況
USD/JPYは現在、重要な価格帯で推移しています。

## テクニカル分析
- トレンド: 上昇基調
- サポート: 145.50
- レジスタンス: 147.00

## 今後の展望
短期的には上昇トレンドが継続する可能性があります。

※これはテスト投稿です。
"""
    
    # 3. Slack通知
    print("\n3. Slack通知:")
    if os.environ.get('ENABLE_PHASE1') == 'true':
        try:
            from src.phase1_alert_system import TradingViewAlertSystem
            
            alert_system = TradingViewAlertSystem()
            test_signal = {
                "action": "BUY",
                "entry_price": 146.50,
                "stop_loss": 146.00,
                "take_profit": 147.00,
                "confidence": 0.85
            }
            
            alert_system.send_slack_alert(test_signal, {
                'currency_pair': 'USD/JPY',
                'market_condition': '上昇トレンド',
                'technical_summary': '全プラットフォーム投稿テスト実行中'
            })
            
            print("   ✅ Slack通知送信完了")
            
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    # 4. Notion投稿
    print("\n4. Notion投稿:")
    try:
        from src.notion_writer import NotionWriter
        
        writer = NotionWriter()
        page_id = writer.create_analysis_page(
            title=f"USD/JPY分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            analysis=analysis_result,
            chart_images=screenshots,
            currency="USD/JPY"
        )
        
        print(f"   ✅ Notionページ作成: {page_id}")
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 5. WordPress投稿
    print("\n5. WordPress投稿:")
    print(f"   URL: {os.environ.get('WORDPRESS_URL')}")
    print(f"   ユーザー: {os.environ.get('WORDPRESS_USERNAME')}")
    
    try:
        from src.blog_publisher import BlogPublisher
        
        # ブログ用フォーマット
        blog_content = f"""**本記事は投資判断を提供するものではありません。**FXチャートの分析手法を学習する目的で、現在のチャート状況を解説しています。実際の売買は自己責任で行ってください。

{analysis_result}

---
※このブログ記事は教育目的で作成されています。投資は自己責任でお願いします。"""
        
        wordpress_config = {
            "url": os.environ.get('WORDPRESS_URL'),
            "username": os.environ.get('WORDPRESS_USERNAME'),
            "password": os.environ.get('WORDPRESS_PASSWORD')
        }
        
        twitter_config = {
            "api_key": os.environ.get('TWITTER_API_KEY'),
            "api_secret": os.environ.get('TWITTER_API_SECRET'),
            "access_token": os.environ.get('TWITTER_ACCESS_TOKEN'),
            "access_token_secret": os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
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
            
        # 6. X (Twitter)投稿結果
        print("\n6. X (Twitter)投稿:")
        if results.get('twitter_url'):
            print(f"   ✅ Twitter投稿成功: {results['twitter_url']}")
        else:
            print("   ❌ Twitter投稿失敗または未実行")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. 結果サマリー
    print("\n" + "="*50)
    print("📊 投稿結果サマリー")
    print("="*50)
    print()
    print("各プラットフォームで投稿を確認してください:")
    print("- Slack: 設定したチャンネル")
    print("- Notion: データベースページ")
    print("- WordPress: https://by-price-action.com の管理画面")
    print("- X (Twitter): @アカウント名 のタイムライン")
    
    print(f"\n完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # 非同期関数を実行
    asyncio.run(post_to_all())