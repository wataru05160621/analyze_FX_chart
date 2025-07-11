#!/usr/bin/env python3
"""
Ollamaを使用したローカルLLM分析
Mac向けの実装
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== Ollama ローカルLLM分析 ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Ollamaのインストール確認
def check_ollama():
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

if not check_ollama():
    print("\n⚠️ Ollamaがインストールされていません")
    print("インストール方法:")
    print("  brew install ollama")
    print("\nインストール後、以下のコマンドでモデルをダウンロード:")
    print("  ollama pull llava")
    sys.exit(1)

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
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher
from src.phase1_alert_system import TradingViewAlertSystem

# 1. チャート生成
print("\n1. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"ollama_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")

# 2. Ollamaで分析
print("\n2. Ollama LLaVA分析...")

def analyze_with_ollama(image_path):
    """Ollamaを使用してチャート画像を分析"""
    prompt = """あなたはFXトレーディングの専門家です。このチャートを詳細に分析してください。

以下の観点から分析してください：
1. 現在のトレンド（上昇/下降/横ばい）
2. サポートとレジスタンスレベル
3. チャートパターン（あれば）
4. 移動平均線との関係
5. 今後の価格動向予測

技術的で具体的な分析を提供してください。"""

    # 画像をbase64エンコード
    import base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # Ollamaコマンドを実行
    cmd = [
        'ollama', 'run', 'llava',
        f'画像を見て分析してください: {prompt}'
    ]
    
    # 別の方法: APIを使用
    try:
        import requests
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llava',
                'prompt': prompt,
                'images': [image_data],
                'stream': False
            }
        )
        if response.status_code == 200:
            return response.json()['response']
    except Exception as e:
        print(f"API エラー: {e}")
    
    # フォールバック: コマンドライン実行
    result = subprocess.run(cmd, capture_output=True, text=True, input=image_data)
    return result.stdout

# 各時間足を分析
analyses = {}
for timeframe, path in screenshots.items():
    print(f"\n  {timeframe}チャート分析中...")
    try:
        analysis = analyze_with_ollama(path)
        analyses[timeframe] = analysis
        print(f"  ✅ {timeframe}分析完了")
    except Exception as e:
        print(f"  ❌ {timeframe}分析エラー: {e}")
        analyses[timeframe] = "分析エラー"

# 3. 総合分析レポート作成
print("\n3. 総合分析レポート作成...")
full_analysis = f"""# USD/JPY テクニカル分析レポート

分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
分析方法: ローカルLLM (Ollama LLaVA)

## 5分足チャート分析

{analyses.get('5min', 'N/A')}

## 1時間足チャート分析

{analyses.get('1hour', 'N/A')}

## 総合的な見解

両時間軸の分析を総合すると、現在のUSD/JPYは重要な局面にあると考えられます。
短期的なトレンドと中期的なトレンドの整合性を確認しながら、慎重にポジションを検討する必要があります。

## リスク管理

- 適切なストップロスの設定を推奨
- ポジションサイズは資金の2%以内に制限
- 重要な経済指標発表時は注意が必要

---
※この分析はローカルLLMによる自動生成です。投資判断は自己責任でお願いします。
"""

# 分析結果を保存
with open('ollama_analysis_result.txt', 'w', encoding='utf-8') as f:
    f.write(full_analysis)

# 4. 各プラットフォームへ投稿
print("\n4. 各プラットフォームへ投稿...")

# Slack通知
print("   Slack通知...")
try:
    alert = TradingViewAlertSystem()
    alert.send_slack_alert(
        {'action': 'INFO', 'entry_price': 0, 'confidence': 0},
        {
            'currency_pair': 'USD/JPY',
            'market_condition': 'ローカルLLM分析完了',
            'technical_summary': f"Ollama LLaVA分析\n時刻: {datetime.now().strftime('%H:%M')}\n{full_analysis[:200]}..."
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
        f"USD/JPY分析 (Ollama) {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
    blog_content = f"""**本記事は投資判断を提供するものではありません。**

ローカルLLM（Ollama LLaVA）を使用したFXチャート分析の実験的な試みです。

{full_analysis}

---
※このブログ記事は教育目的で作成されています。ローカルLLMによる自動分析のため、精度には限界があります。"""

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
print("\n結果:")
print(f"- 分析結果: ollama_analysis_result.txt")
print(f"- チャート画像: {output_dir}")
print("\n注意:")
print("- Ollama LLaVAの分析品質はClaude APIより劣る可能性があります")
print("- より高品質な分析にはGPUメモリ24GB以上推奨")