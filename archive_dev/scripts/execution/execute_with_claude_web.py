#!/usr/bin/env python3
"""
Claude.ai Web版を使用した分析
Seleniumによる自動化
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== Claude.ai Web版分析 ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n注意: Chromeブラウザが開きます。手動でログインが必要な場合があります。")

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
output_dir = Path('screenshots') / f"claude_web_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")

# 2. Claude.ai Web分析
print("\n2. Claude.ai Web分析...")

def analyze_with_claude_web(screenshots):
    """Claude.ai Webを使用してチャート画像を分析"""
    
    # Chromeドライバーの設定
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # ヘッドレスモードは使用しない（ログインが必要なため）
    
    driver = webdriver.Chrome(options=options)
    analysis_results = {}
    
    try:
        # Claude.aiにアクセス
        driver.get("https://claude.ai/new")
        
        print("\n⚠️ ブラウザでClaude.aiにログインしてください")
        print("ログイン完了後、Enterキーを押してください...")
        input()
        
        # 各チャートを分析
        for timeframe, image_path in screenshots.items():
            print(f"\n{timeframe}チャートを分析中...")
            
            # 新しいチャットを開始
            try:
                new_chat_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'New chat')]"))
                )
                new_chat_button.click()
                time.sleep(2)
            except:
                # 既に新しいチャット画面の場合
                pass
            
            # ファイルアップロードボタンを探す
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # 画像をアップロード
            file_input.send_keys(str(image_path))
            time.sleep(2)
            
            # プロンプトを入力
            prompt = f"""このFXチャート（{timeframe}）を詳細に分析してください。

以下の観点から分析してください：
1. 現在のトレンド方向と強さ
2. 重要なサポート・レジスタンスレベル
3. チャートパターンの識別
4. 移動平均線との関係性
5. エントリーポイントの提案
6. リスク管理の観点からの注意点

プライスアクションの原則に基づいた、実践的な分析をお願いします。"""
            
            # テキストエリアを探してプロンプトを入力
            text_area = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )
            text_area.send_keys(prompt)
            text_area.send_keys(Keys.RETURN)
            
            # 応答を待つ（最大60秒）
            print("Claudeの応答を待っています...")
            time.sleep(10)  # 初期待機
            
            # 応答の取得を試みる
            max_wait = 60
            start_time = time.time()
            response_text = ""
            
            while time.time() - start_time < max_wait:
                try:
                    # Claudeの応答を取得
                    response_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='message-content']")
                    if len(response_elements) > 1:  # ユーザーメッセージの後の応答
                        response_text = response_elements[-1].text
                        if len(response_text) > 100:  # 十分な長さの応答
                            break
                except:
                    pass
                time.sleep(2)
            
            if response_text:
                analysis_results[timeframe] = response_text
                print(f"✅ {timeframe}分析完了 ({len(response_text)}文字)")
            else:
                analysis_results[timeframe] = "分析の取得に失敗しました"
                print(f"❌ {timeframe}分析失敗")
            
            time.sleep(5)  # 次の分析前に待機
            
    except Exception as e:
        print(f"❌ Web分析エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
    
    return analysis_results

# Web分析実行
analyses = analyze_with_claude_web(screenshots)

# 3. 総合分析レポート作成
print("\n3. 総合分析レポート作成...")
full_analysis = f"""# USD/JPY テクニカル分析レポート

分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
分析方法: Claude.ai Web版

## 5分足チャート分析

{analyses.get('5min', '分析なし')}

## 1時間足チャート分析

{analyses.get('1hour', '分析なし')}

## 総括

両時間軸の分析結果を踏まえ、現在のUSD/JPYの取引戦略を慎重に検討する必要があります。
短期と中期のトレンドの整合性を確認し、適切なリスク管理を行うことが重要です。

---
※この分析はClaude.ai Web版を使用した自動分析です。投資判断は自己責任でお願いします。
"""

# 分析結果を保存
with open('claude_web_analysis_result.txt', 'w', encoding='utf-8') as f:
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
            'market_condition': 'Claude Web分析完了',
            'technical_summary': f"Claude.ai Web版分析\n時刻: {datetime.now().strftime('%H:%M')}\n{full_analysis[:200]}..."
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
        f"USD/JPY分析 (Claude Web) {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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

Claude.ai Web版を使用したFXチャート分析です。

{full_analysis}

---
※このブログ記事は教育目的で作成されています。"""

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
print(f"- 分析結果: claude_web_analysis_result.txt")
print(f"- チャート画像: {output_dir}")
print("\nSeleniumドライバーが必要な場合:")
print("pip install selenium")
print("brew install chromedriver")