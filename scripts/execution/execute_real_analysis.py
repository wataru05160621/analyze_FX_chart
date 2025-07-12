#!/usr/bin/env python3
"""
実際のFX分析を実行して全プラットフォームに投稿
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境変数を設定
def setup_environment():
    """環境変数を設定"""
    # .envファイル読み込み
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value and value not in ['your_value_here', 'your_api_key_here']:
                        os.environ[key] = value
    
    # .env.phase1読み込み
    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # 8時モードを設定（ブログ投稿を有効化）
    os.environ['FORCE_HOUR'] = '8'
    os.environ['ENABLE_BLOG_POSTING'] = 'true'

async def execute_real_analysis():
    """実際の分析を実行"""
    
    print("=== FX分析システム 実分析実行 ===")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 環境変数設定
    setup_environment()
    
    try:
        # main_multi_currencyの処理を直接実行
        from src.chart_generator import ChartGenerator
        from src.claude_analyzer import ClaudeAnalyzer
        from src.notion_writer import NotionWriter
        from src.blog_publisher import BlogPublisher
        from src.phase1_alert_system import SignalGenerator, TradingViewAlertSystem
        from src.phase1_performance_automation import Phase1PerformanceAutomation
        
        # 1. チャート生成
        print("1. チャート生成中...")
        generator = ChartGenerator('USDJPY=X')
        screenshot_dir = Path("screenshots") / datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        screenshots = generator.generate_multiple_charts(
            timeframes=['5min', '1hour'],
            output_dir=screenshot_dir,
            candle_count=288
        )
        print(f"   ✅ チャート生成完了")
        for tf, path in screenshots.items():
            print(f"      {tf}: {path}")
        
        # 2. Claude分析
        print("\n2. Claude API分析中...")
        analyzer = ClaudeAnalyzer()
        
        # PDFコンテンツ確認
        if analyzer.book_content:
            print(f"   ✅ プライスアクションの原則PDF読み込み済み: {len(analyzer.book_content)}文字")
        
        analysis_result = analyzer.analyze_charts(screenshots)
        print(f"   ✅ 分析完了: {len(analysis_result)}文字")
        
        # 分析結果を保存
        with open('latest_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(analysis_result)
        
        # 3. Phase 1 (Slack通知)
        print("\n3. Slack通知送信中...")
        if os.environ.get('ENABLE_PHASE1') == 'true':
            try:
                # シグナル生成
                signal_generator = SignalGenerator()
                signal = signal_generator.generate_trading_signal(analysis_result)
                
                # アラート送信
                alert_system = TradingViewAlertSystem()
                alert_system.send_slack_alert(signal, {
                    'currency_pair': 'USD/JPY',
                    'market_condition': '実分析結果',
                    'technical_summary': analysis_result[:500] + '...'
                })
                
                # パフォーマンス記録
                if signal['action'] != 'NONE':
                    performance = Phase1PerformanceAutomation()
                    signal_id = performance.record_signal(signal, {
                        'summary': analysis_result,
                        'currency_pair': 'USD/JPY'
                    })
                    print(f"   ✅ Slack通知送信 & シグナル記録: {signal_id}")
                else:
                    print("   ✅ Slack通知送信（シグナルなし）")
                    
            except Exception as e:
                print(f"   ❌ エラー: {e}")
        
        # 4. Notion投稿
        print("\n4. Notion投稿中...")
        try:
            writer = NotionWriter()
            page_id = writer.create_analysis_page(
                title=f"USD/JPY分析_{datetime.now().strftime('%Y%m%d_%H%M')}",
                analysis=analysis_result,
                chart_images=screenshots,
                currency="USD/JPY"
            )
            print(f"   ✅ Notionページ作成: {page_id}")
            
        except Exception as e:
            print(f"   ❌ エラー: {e}")
        
        # 5. ブログ投稿（WordPress）
        print("\n5. WordPress投稿中...")
        if os.environ.get('ENABLE_BLOG_POSTING') == 'true':
            try:
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
                
                # ログ有効化
                import logging
                logging.basicConfig(level=logging.INFO)
                
                publish_results = publisher.publish_analysis(blog_content, screenshots)
                
                if publish_results.get('wordpress_url'):
                    print(f"   ✅ WordPress投稿成功: {publish_results['wordpress_url']}")
                else:
                    print("   ❌ WordPress投稿失敗")
                
                # 6. Twitter投稿結果
                if publish_results.get('twitter_url'):
                    print(f"\n6. Twitter投稿:")
                    print(f"   ✅ Twitter投稿成功: {publish_results['twitter_url']}")
                    
            except Exception as e:
                print(f"   ❌ ブログ投稿エラー: {e}")
                import traceback
                traceback.print_exc()
        
        # 7. 結果サマリー
        print("\n" + "="*60)
        print("📊 実分析投稿完了")
        print("="*60)
        print()
        print("✅ 実行した処理:")
        print(f"   - チャート生成: 2枚（5分足、1時間足）")
        print(f"   - Claude分析: {len(analysis_result)}文字")
        print(f"   - 画像保存先: {screenshot_dir}")
        print()
        print("📍 投稿先確認:")
        print("   - Slack: 設定したチャンネルを確認")
        print("   - Notion: データベースで最新ページを確認")
        print("   - WordPress: https://by-price-action.com/wp-admin/")
        print("   - Twitter: タイムラインを確認")
        print()
        print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 非同期関数を実行
    asyncio.run(execute_real_analysis())