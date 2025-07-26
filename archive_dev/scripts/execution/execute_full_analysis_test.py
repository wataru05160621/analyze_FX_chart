#!/usr/bin/env python3
"""
Volmanメソッドに基づく完全な分析テスト
ブラッシュアップされた分析内容の出力確認
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== Volmanメソッド完全分析テスト ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数読み込み
print("\n1. 環境変数読み込み...")
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            # コメントを除去
            if '#' in line:
                line = line.split('#')[0].strip()
            key, value = line.strip().split('=', 1)
            if value and value not in ['your_value_here', 'your_api_key_here']:
                os.environ[key] = value

with open('.env.phase1', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# APIキー確認
api_key = os.environ.get('CLAUDE_API_KEY')
if not api_key:
    print("❌ CLAUDE_API_KEYが見つかりません")
    sys.exit(1)
else:
    print(f"✅ Claude API キー確認済み")

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher

# 2. チャート生成
print("\n2. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"volman_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")
for tf, path in screenshots.items():
    print(f"   {tf}: {path}")

# 3. Claude分析（Volmanメソッド）
print("\n3. Claude分析（Volmanメソッド）...")
analyzer = ClaudeAnalyzer()

print("   マークダウンファイルの読み込み状況:")
if analyzer.book_content:
    print(f"   ✅ Volmanメソッドコンテンツ読み込み済み: {len(analyzer.book_content)}文字")
else:
    print("   ⚠️ Volmanメソッドコンテンツが読み込まれていません")

try:
    analysis = analyzer.analyze_charts(screenshots)
    print(f"   ✅ 分析完了: {len(analysis)}文字")
    
    # 分析結果の重要部分を表示
    print("\n=== 分析結果プレビュー ===")
    print(analysis[:1000])
    print("\n... (以下省略) ...\n")
    
    # 重要な要素の確認
    print("=== 分析品質チェック ===")
    checks = {
        "Volmanメソッド言及": "Volman" in analysis,
        "25EMA分析": "25EMA" in analysis,
        "ビルドアップ分析": "ビルドアップ" in analysis,
        "セットアップ識別": "セットアップ" in analysis,
        "20/10ブラケット": "20pips" in analysis or "10pips" in analysis,
        "星評価": "⭐" in analysis,
        "価格レベル記載": any(char.isdigit() and '.' in analysis[max(0, i-5):i+5] for i, char in enumerate(analysis)),
        "リスク管理言及": "リスク" in analysis or "ストップロス" in analysis
    }
    
    for check, result in checks.items():
        print(f"   {check}: {'✅' if result else '❌'}")
    
except Exception as e:
    print(f"   ❌ 分析エラー: {e}")
    import traceback
    traceback.print_exc()
    analysis = None

# 分析結果を保存
if analysis:
    with open('volman_analysis_result.txt', 'w', encoding='utf-8') as f:
        f.write(f"分析日時: {datetime.now()}\n")
        f.write(f"チャート画像: {output_dir}\n\n")
        f.write(analysis)
    print(f"\n✅ 分析結果保存: volman_analysis_result.txt")

# 4. 各プラットフォームへのテスト投稿
print("\n4. 各プラットフォームへのテスト投稿...")

if analysis:
    # Slack通知テスト
    print("\n   Slack通知テスト...")
    try:
        import requests
        webhook = os.environ.get('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/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')
        
        # 分析サマリー抽出
        summary_lines = []
        if "現在価格" in analysis:
            import re
            price_match = re.search(r'現在価格[：:]\s*([\d.]+)', analysis)
            if price_match:
                summary_lines.append(f"USD/JPY: {price_match.group(1)}")
        
        if "⭐⭐⭐⭐⭐" in analysis:
            summary_lines.append("セットアップ品質: ⭐⭐⭐⭐⭐ (完璧)")
        elif "⭐⭐⭐⭐" in analysis:
            summary_lines.append("セットアップ品質: ⭐⭐⭐⭐☆ (優秀)")
        
        message = {
            "text": f"*Volmanメソッド分析完了*\n時刻: {datetime.now().strftime('%H:%M')}\n" + "\n".join(summary_lines[:3])
        }
        
        resp = requests.post(webhook, json=message)
        if resp.status_code == 200:
            print("   ✅ Slack送信成功")
        else:
            print(f"   ❌ Slack送信失敗: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Slackエラー: {e}")

    # Notion投稿テスト
    print("\n   Notion投稿テスト...")
    try:
        writer = NotionWriter()
        page_id = writer.create_analysis_page(
            f"USD/JPY Volman分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            analysis,
            screenshots,
            "USD/JPY"
        )
        print(f"   ✅ Notion投稿成功: {page_id}")
    except Exception as e:
        print(f"   ❌ Notionエラー: {e}")

    # WordPress投稿テスト
    print("\n   WordPress投稿テスト...")
    try:
        blog_content = f"""{analysis}

---
※このブログ記事は教育目的で作成されています。投資は自己責任でお願いします。
※分析手法: Bob Volman「Forex Price Action Scalping」メソッド"""

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
            print(f"   ✅ WordPress投稿成功: {results['wordpress_url']}")
            
            # Twitter投稿内容の確認
            if results.get('twitter_url'):
                print(f"   ✅ Twitter投稿成功: {results['twitter_url']}")
            else:
                print("   ℹ️ Twitter投稿はスキップされました")
        else:
            print("   ❌ WordPress投稿失敗")
            
    except Exception as e:
        print(f"   ❌ 投稿エラー: {e}")
        import traceback
        traceback.print_exc()

# 5. 分析品質レポート
print("\n=== 分析品質レポート ===")
print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"チャート画像: {output_dir}")
print(f"分析結果: volman_analysis_result.txt")

if analysis:
    # Volmanメソッドの特徴的な要素をカウント
    volman_elements = {
        "25EMA言及回数": analysis.count("25EMA"),
        "ビルドアップ言及回数": analysis.count("ビルドアップ"),
        "セットアップ言及回数": analysis.count("セットアップ"),
        "20pips/10pips言及": analysis.count("20pips") + analysis.count("10pips"),
        "スキップ判断言及": analysis.count("スキップ"),
        "ATR言及": analysis.count("ATR"),
        "星評価使用": "⭐" in analysis
    }
    
    print("\nVolmanメソッド要素の使用状況:")
    for element, count in volman_elements.items():
        if isinstance(count, bool):
            print(f"   {element}: {'✅' if count else '❌'}")
        else:
            print(f"   {element}: {count}回")

print("\n✅ 全テスト完了!")
print("\n次のステップ:")
print("1. volman_analysis_result.txt で詳細な分析内容を確認")
print("2. 各プラットフォームで投稿内容を確認")
print("3. 必要に応じてプロンプトを調整")