#!/usr/bin/env python3
"""
Claude Haiku APIを使用した高品質分析（修正版）
環境変数の問題を解決
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
import anthropic
import base64

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== Claude Haiku高品質分析（修正版） ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数読み込み（修正版）
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            # コメントを除去
            if '#' in line:
                line = line.split('#')[0].strip()
            key, value = line.strip().split('=', 1)
            if value and value not in ['your_value_here', 'your_api_key_here']:
                os.environ[key] = value

# ANTHROPIC_API_KEYをCLAUDE_API_KEYから設定
if 'CLAUDE_API_KEY' in os.environ and 'ANTHROPIC_API_KEY' not in os.environ:
    os.environ['ANTHROPIC_API_KEY'] = os.environ['CLAUDE_API_KEY']

with open('.env.phase1', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

# API キーの確認
api_key = os.environ.get('CLAUDE_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    print("❌ Claude API キーが見つかりません")
    sys.exit(1)
else:
    print(f"✅ API キー確認済み: {api_key[:10]}...")

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher
from src.pdf_extractor import PDFExtractor

# 1. プライスアクションの原則を読み込み
print("\n1. プライスアクションの原則PDF読み込み...")
book_content = ""
try:
    pdf_path = Path("doc") / "プライスアクションの原則.pdf"
    if pdf_path.exists():
        pdf_extractor = PDFExtractor(pdf_path)
        book_content = pdf_extractor.extract_text()
        print(f"✅ PDF読み込み完了: {len(book_content)}文字")
    else:
        print("⚠️ PDFファイルが見つかりません")
except Exception as e:
    print(f"❌ PDF読み込みエラー: {e}")

# 2. チャート生成
print("\n2. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"haiku_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")

# 3. Claude Haiku分析
print("\n3. Claude Haiku分析...")

def create_enhanced_prompt(timeframe, book_excerpt):
    """詳細プロンプト"""
    
    return f"""あなたは経験豊富なFXトレーダーです。以下の参考書籍の内容に基づいて、{timeframe}チャートを詳細に分析してください。

# 参考書籍（抜粋）:
{book_excerpt[:15000]}

# 分析要件:

## 1. 市場構造分析
- 全体的なトレンド方向
- 主要なサポート・レジスタンスレベル（具体的な価格）
- チャートパターン

## 2. 移動平均線分析
- 25EMA、75EMA、200EMAの位置関係
- 価格との相互作用

## 3. トレード戦略
### 上昇シナリオ
- エントリー: [具体的価格]
- ターゲット: [価格]
- ストップロス: [価格]

### 下降シナリオ
- エントリー: [具体的価格]
- ターゲット: [価格]
- ストップロス: [価格]

## 4. リスク管理
- ポジションサイズ: 口座の1-2%
- 注意事項

具体的な価格レベルを必ず含めてください。"""

async def analyze_with_haiku(image_path, timeframe):
    """Haiku分析（修正版）"""
    
    # 画像をbase64エンコード
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # PDFコンテンツ
    book_excerpt = book_content[:15000] if book_content else ""
    
    # プロンプト
    prompt = create_enhanced_prompt(timeframe, book_excerpt)
    
    try:
        # APIキーを明示的に指定
        client = anthropic.Anthropic(
            api_key=api_key
        )
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"Haiku APIエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

# 非同期実行
async def run_analysis():
    analyses = {}
    total_cost = 0
    
    for timeframe, path in screenshots.items():
        print(f"\n  {timeframe}チャート分析中...")
        try:
            analysis = await analyze_with_haiku(path, timeframe)
            if analysis:
                analyses[timeframe] = analysis
                print(f"  ✅ {timeframe}分析完了 ({len(analysis)}文字)")
                total_cost += 0.0005
            else:
                analyses[timeframe] = "分析エラー"
                print(f"  ❌ {timeframe}分析失敗")
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            analyses[timeframe] = "分析エラー"
    
    return analyses, total_cost

# 分析実行
analyses, total_cost = asyncio.run(run_analysis())
print(f"\n推定コスト: ${total_cost:.4f}")

# 4. レポート作成
print("\n4. ブログ品質レポート作成...")

full_analysis = f"""# USD/JPY テクニカル分析レポート

分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
分析手法: プライスアクション理論に基づく詳細分析

## 市場概況

本日のUSD/JPYは、複数の時間軸で重要な局面を迎えています。

## 5分足チャート分析

{analyses.get('5min', 'N/A')}

## 1時間足チャート分析

{analyses.get('1hour', 'N/A')}

## 総合判断

両時間軸の分析を総合し、慎重なトレード戦略を推奨します。

### リスク管理の重要性

- ストップロスの徹底
- ポジションサイズ管理（口座の1-2%）
- 重要指標発表時の注意

---
※本記事は教育目的で作成されており、投資助言ではありません。
"""

# 分析結果を保存
with open('haiku_fixed_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(full_analysis)

# 5. 各プラットフォームへ投稿
print("\n5. 各プラットフォームへ投稿...")

# Slack通知（修正版）
print("   Slack通知...")
try:
    from src.phase1_notification import Phase1NotificationSystem
    notification = Phase1NotificationSystem()
    notification.send_completion_notification(
        "USD/JPY",
        {
            'analysis': full_analysis[:500],
            'chart_paths': screenshots
        }
    )
    print("   ✅ Slack送信完了")
except Exception as e:
    print(f"   ❌ Slackエラー: {e}")
    # 直接Webhook送信を試みる
    try:
        import requests
        webhook = "https://hooks.slack.com/services/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"
        message = {
            "text": f"*FX分析完了* (Haiku)\n時刻: {datetime.now().strftime('%H:%M')}\n{full_analysis[:200]}..."
        }
        resp = requests.post(webhook, json=message)
        if resp.status_code == 200:
            print("   ✅ Slack送信完了（直接）")
    except:
        pass

# Notion投稿
print("   Notion投稿...")
try:
    writer = NotionWriter()
    page_id = writer.create_analysis_page(
        f"USD/JPY分析 (Haiku) {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        full_analysis,
        screenshots,
        "USD/JPY"
    )
    print(f"   ✅ Notion投稿完了: {page_id}")
except Exception as e:
    print(f"   ❌ Notionエラー: {e}")

# WordPress投稿
print("   WordPress投稿...")
try:
    blog_content = f"""{full_analysis}"""

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
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    results = publisher.publish_analysis(blog_content, screenshots)
    
    if results.get('wordpress_url'):
        print(f"   ✅ WordPress投稿: {results['wordpress_url']}")
        
except Exception as e:
    print(f"   ❌ 投稿エラー: {e}")

print("\n✅ 処理完了!")
print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n結果:")
print(f"- 分析結果: haiku_fixed_analysis.txt")
print(f"- チャート画像: {output_dir}")
print(f"- コスト: ${total_cost:.4f}")
print(f"\n修正内容:")
print("1. API キー環境変数の問題を解決")
print("2. WordPress設定のコメント除去")
print("3. Slack通知の修正")