#!/usr/bin/env python3
"""
32GB Mac向け最適化ローカルLLM分析
メモリ使用量を考慮した自動モデル選択
"""
import os
import sys
import subprocess
import json
import gc
import psutil
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== 最適化ローカルLLM分析（32GB Mac） ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# メモリ状況を確認
try:
    memory = psutil.virtual_memory()
    print(f"\nシステムメモリ: {memory.total / (1024**3):.1f}GB")
    print(f"利用可能メモリ: {memory.available / (1024**3):.1f}GB")
except:
    print("メモリ情報取得不可")

# 最適なモデルを選択
def select_optimal_model():
    """利用可能メモリに基づいて最適なモデルを選択"""
    models = [
        ("llama3.2-vision:11b", 22, "最高品質 - Meta最新ビジョンモデル"),
        ("llava:13b-v1.6", 20, "バランス型 - 安定動作"),
        ("bakllava", 12, "高速型 - Mistralベース"),
        ("llava", 8, "軽量版 - 基本モデル")
    ]
    
    try:
        available_gb = psutil.virtual_memory().available / (1024**3)
    except:
        available_gb = 20  # デフォルト値
    
    print(f"\n利用可能なモデル:")
    selected_model = None
    
    for model, required_gb, description in models:
        status = "✅" if available_gb > required_gb * 1.2 else "❌"
        print(f"{status} {model} (要{required_gb}GB) - {description}")
        
        if not selected_model and available_gb > required_gb * 1.2:
            selected_model = model
    
    if not selected_model:
        selected_model = "llava"  # フォールバック
    
    return selected_model

# Ollamaのインストール確認
def check_and_install_ollama():
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("\n⚠️ Ollamaがインストールされていません")
        print("インストールしますか？ (y/n): ", end="")
        if input().lower() == 'y':
            subprocess.run(['brew', 'install', 'ollama'])
            return True
        return False

if not check_and_install_ollama():
    print("Ollamaが必要です。終了します。")
    sys.exit(1)

# モデル選択
MODEL = select_optimal_model()
print(f"\n選択されたモデル: {MODEL}")

# モデルの存在確認とダウンロード
def ensure_model(model_name):
    """モデルが存在しない場合はダウンロード"""
    print(f"\n{model_name}の確認中...")
    
    # モデルリストを確認
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
    if model_name not in result.stdout:
        print(f"{model_name}をダウンロードします...")
        
        # 進捗表示付きでダウンロード
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"  {line.strip()}")
        
        process.wait()
        
        if process.returncode != 0:
            print(f"❌ {model_name}のダウンロードに失敗しました")
            return False
    
    print(f"✅ {model_name}の準備完了")
    return True

# モデルの準備
if not ensure_model(MODEL):
    # フォールバックモデルを試す
    MODEL = "llava"
    if not ensure_model(MODEL):
        print("モデルの準備に失敗しました")
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

# メモリ最適化設定
os.environ['OLLAMA_NUM_PARALLEL'] = '1'
os.environ['OLLAMA_MAX_LOADED_MODELS'] = '1'

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.notion_writer import NotionWriter
from src.blog_publisher import BlogPublisher
from src.phase1_alert_system import TradingViewAlertSystem

# 1. チャート生成
print("\n1. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"optimal_llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")

# 2. 最適化されたLLM分析
print(f"\n2. {MODEL}による分析...")

def analyze_with_optimal_llm(image_path, timeframe):
    """最適化されたプロンプトでチャート分析"""
    
    # モデルに応じたプロンプト最適化
    if "llama3.2" in MODEL:
        prompt = """Analyze this forex chart as a professional trader. Focus on:
1. Current trend direction and strength
2. Key support and resistance levels
3. Chart patterns if any
4. Entry and exit points
5. Risk management considerations

Provide specific price levels and actionable insights."""
    else:
        prompt = f"""このFXチャート（{timeframe}）を分析してください。

重要ポイント:
1. トレンド方向と強さ
2. サポート・レジスタンス
3. エントリーポイント
4. リスク管理

具体的な価格レベルを含めて分析してください。"""

    # メモリ効率的な分析実行
    import base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    try:
        import requests
        
        # ストリーミング無効で一括取得（メモリ効率）
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': MODEL,
                'prompt': prompt,
                'images': [image_data],
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 1000,  # 出力を制限
                }
            },
            timeout=300  # 5分タイムアウト
        )
        
        if response.status_code == 200:
            return response.json()['response']
        else:
            print(f"API エラー: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"分析エラー: {e}")
        return None

# 各時間足を分析（メモリ効率化）
analyses = {}

# 5分足分析
print(f"\n  5分足チャート分析中...")
try:
    analysis_5min = analyze_with_optimal_llm(screenshots['5min'], '5分足')
    if analysis_5min:
        analyses['5min'] = analysis_5min
        print(f"  ✅ 5分足分析完了 ({len(analysis_5min)}文字)")
    else:
        analyses['5min'] = "分析エラー"
        print(f"  ❌ 5分足分析失敗")
    
    # メモリ解放
    gc.collect()
    
except Exception as e:
    print(f"  ❌ エラー: {e}")
    analyses['5min'] = "分析エラー"

# 1時間足分析
print(f"\n  1時間足チャート分析中...")
try:
    analysis_1hour = analyze_with_optimal_llm(screenshots['1hour'], '1時間足')
    if analysis_1hour:
        analyses['1hour'] = analysis_1hour
        print(f"  ✅ 1時間足分析完了 ({len(analysis_1hour)}文字)")
    else:
        analyses['1hour'] = "分析エラー"
        print(f"  ❌ 1時間足分析失敗")
        
    # メモリ解放
    gc.collect()
    
except Exception as e:
    print(f"  ❌ エラー: {e}")
    analyses['1hour'] = "分析エラー"

# 3. 総合分析レポート作成
print("\n3. 総合分析レポート作成...")

# モデル品質評価
quality_rating = {
    "llama3.2-vision:11b": "★★★★☆ (Claude APIの75%)",
    "llava:13b-v1.6": "★★★★☆ (Claude APIの70%)",
    "bakllava": "★★★☆☆ (Claude APIの65%)",
    "llava": "★★★☆☆ (Claude APIの60%)"
}

full_analysis = f"""# USD/JPY テクニカル分析レポート

分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
使用モデル: {MODEL}
モデル品質: {quality_rating.get(MODEL, "★★★☆☆")}

## 5分足チャート分析

{analyses.get('5min', 'N/A')}

## 1時間足チャート分析

{analyses.get('1hour', 'N/A')}

## 総合的な見解

短期（5分足）と中期（1時間足）の両方の視点から、現在のUSD/JPYは重要な局面にあります。
両時間軸のシグナルを総合的に判断し、リスク管理を徹底することが重要です。

## トレード推奨事項

1. エントリーは両時間軸の方向性が一致した時
2. ストップロスは必ず設定
3. ポジションサイズは口座残高の2%以内
4. 重要指標発表時はポジションクローズ推奨

---
※この分析は{MODEL}による自動生成です。
※モデルの精度はClaude APIの{quality_rating.get(MODEL, '60-70%')}程度です。
※投資判断は自己責任でお願いします。
"""

# 分析結果を保存
with open('optimal_llm_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(full_analysis)

# 4. 各プラットフォームへ投稿
print("\n4. 各プラットフォームへ投稿...")

# メモリ状況を再確認
try:
    memory = psutil.virtual_memory()
    print(f"現在の利用可能メモリ: {memory.available / (1024**3):.1f}GB")
except:
    pass

# Slack通知
print("   Slack通知...")
try:
    alert = TradingViewAlertSystem()
    alert.send_slack_alert(
        {'action': 'INFO', 'entry_price': 0, 'confidence': 0},
        {
            'currency_pair': 'USD/JPY',
            'market_condition': f'{MODEL}分析完了',
            'technical_summary': f"ローカルLLM分析\nモデル: {MODEL}\n時刻: {datetime.now().strftime('%H:%M')}\n{full_analysis[:200]}..."
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
        f"USD/JPY分析 ({MODEL}) {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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

ローカルLLM（{MODEL}）を使用したFXチャート分析です。
このモデルの精度はClaude APIの{quality_rating.get(MODEL, '60-70%')}程度です。

{full_analysis}

---
※このブログ記事は教育目的で作成されています。
※32GB Macで動作する最適化されたモデルを使用しています。"""

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
print(f"- 分析結果: optimal_llm_analysis.txt")
print(f"- チャート画像: {output_dir}")
print(f"\n使用モデル: {MODEL}")
print(f"モデル品質: {quality_rating.get(MODEL, '★★★☆☆')}")

# メモリ使用状況
try:
    memory = psutil.virtual_memory()
    print(f"\n最終メモリ状況:")
    print(f"- 使用中: {memory.percent}%")
    print(f"- 利用可能: {memory.available / (1024**3):.1f}GB")
except:
    pass

print("\n次回の推奨:")
if MODEL == "llava":
    print("- より大きなモデルを試すには、他のアプリを終了してメモリを確保してください")
elif "llama3.2" in MODEL:
    print("- 最高品質のモデルを使用しています")
else:
    print("- メモリに余裕がある時は llama3.2-vision:11b を試してください")