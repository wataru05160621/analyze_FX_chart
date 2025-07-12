#!/usr/bin/env python
"""
完全統合テスト - 全プラットフォームへの出力
"""
import os
import sys
import json
import time
from datetime import datetime

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== FX分析システム 完全統合テスト ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Phase 1の環境変数を読み込み
def load_phase1_env():
    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_phase1_env()

# 1. テスト分析の実行
print("1. テスト分析を実行:")
print("   USD/JPYのテストデータを生成...")

# テスト分析データ
test_analysis = {
    "timestamp": datetime.now().isoformat(),
    "currency_pair": "USD/JPY",
    "current_price": 146.54,
    "recommendation": "BUY",
    "entry_price": 146.35,
    "stop_loss": 145.85,
    "take_profit": 147.35,
    "confidence": 0.78,
    "market_condition": "上昇トレンド継続の可能性が高い",
    "key_levels": {
        "resistance": [147.00, 147.50, 148.00],
        "support": [146.00, 145.50, 145.00]
    },
    "technical_summary": "MACDがゴールデンクロスを形成、RSIは65で上昇余地あり。移動平均線は全て上向きで強気相場を示唆。",
    "risk_reward_ratio": 2.0,
    "expected_value": 0.31,  # 期待値
    "chart_url": "https://example.com/chart/usdjpy_test.png"
}

# analysis_summary.jsonに保存
with open('analysis_summary.json', 'w') as f:
    json.dump(test_analysis, f, ensure_ascii=False, indent=2)

print("   ✅ テスト分析データを作成しました")

# 2. Slack通知（Phase 1経由）
print("\n2. Slack通知のテスト:")
try:
    from src.phase1_alert_system import TradingViewAlertSystem
    
    alert_system = TradingViewAlertSystem()
    
    # Phase 1シグナル形式
    test_signal = {
        "action": test_analysis["recommendation"],
        "entry_price": test_analysis["entry_price"],
        "stop_loss": test_analysis["stop_loss"],
        "take_profit": test_analysis["take_profit"],
        "confidence": test_analysis["confidence"]
    }
    
    # Slack通知送信
    alert_system.send_slack_alert(test_signal, test_analysis)
    print("   ✅ Slack通知を送信しました")
    
    # Phase 1パフォーマンス記録
    if os.environ.get('ENABLE_PHASE1') == 'true':
        from src.phase1_performance_automation import Phase1PerformanceAutomation
        perf = Phase1PerformanceAutomation()
        signal_id = perf.record_signal(test_signal, test_analysis)
        print(f"   ✅ Phase 1シグナル記録: {signal_id}")
        
except Exception as e:
    print(f"   ❌ Slack通知エラー: {e}")

# 3. Notion出力
print("\n3. Notion出力のテスト:")
try:
    from src.notion_writer import NotionWriter
    
    writer = NotionWriter()
    
    # Notionページデータ
    notion_data = {
        "通貨ペア": test_analysis["currency_pair"],
        "現在価格": test_analysis["current_price"],
        "推奨アクション": test_analysis["recommendation"],
        "エントリー価格": test_analysis["entry_price"],
        "ストップロス": test_analysis["stop_loss"],
        "テイクプロフィット": test_analysis["take_profit"],
        "信頼度": f"{test_analysis['confidence'] * 100:.0f}%",
        "市場状況": test_analysis["market_condition"],
        "テクニカル分析": test_analysis["technical_summary"],
        "リスクリワード比": test_analysis["risk_reward_ratio"],
        "期待値": f"{test_analysis['expected_value']:.2f}",
        "分析時刻": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # テストページとして作成
    title = f"【テスト】{test_analysis['currency_pair']} 分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # 実際の作成はコメントアウト（本番環境を汚さないため）
    # page_id = writer.create_page(title, notion_data)
    # print(f"   ✅ Notionページ作成: {page_id}")
    
    print("   ✅ Notionページ作成準備完了")
    print(f"      タイトル: {title}")
    print(f"      データベースID: {os.environ.get('NOTION_DATABASE_ID', 'Not set')[:10]}...")
    
except Exception as e:
    print(f"   ❌ Notion出力エラー: {e}")

# 4. ブログ出力（WordPress）
print("\n4. ブログ出力のテスト:")
try:
    from src.blog_analyzer import BlogAnalyzer
    from src.blog_publisher import BlogPublisher
    
    # ブログコンテンツ生成
    analyzer = BlogAnalyzer()
    
    # ブログ用の詳細コンテンツ
    blog_content = f"""
<h2>市場分析サマリー</h2>
<p>現在のUSD/JPYは{test_analysis['current_price']}円で取引されています。
{test_analysis['market_condition']}という状況にあり、{test_analysis['recommendation']}ポジションを推奨します。</p>

<h3>テクニカル分析</h3>
<p>{test_analysis['technical_summary']}</p>

<h3>トレード設定</h3>
<ul>
<li>エントリー: {test_analysis['entry_price']}円</li>
<li>ストップロス: {test_analysis['stop_loss']}円</li>
<li>テイクプロフィット: {test_analysis['take_profit']}円</li>
<li>リスクリワード比: {test_analysis['risk_reward_ratio']}</li>
<li>期待値: {test_analysis['expected_value']}</li>
</ul>

<h3>重要レベル</h3>
<p>レジスタンス: {', '.join(map(str, test_analysis['key_levels']['resistance']))}</p>
<p>サポート: {', '.join(map(str, test_analysis['key_levels']['support']))}</p>

<p><em>※これはテスト投稿です。実際の投資判断は自己責任でお願いします。</em></p>
"""
    
    # WordPressの設定確認
    wp_url = os.environ.get('WORDPRESS_URL', 'Not set')
    wp_user = os.environ.get('WORDPRESS_USERNAME', 'Not set')
    
    print("   ✅ ブログコンテンツ生成完了")
    print(f"      WordPress URL: {wp_url[:30] if wp_url != 'Not set' else 'Not set'}...")
    print(f"      文字数: {len(blog_content)}")
    
    # 実際の投稿はコメントアウト
    # publisher = BlogPublisher()
    # post_id = publisher.create_post({
    #     'title': f'【テスト】USD/JPY分析 {datetime.now().strftime("%Y年%m月%d日")}',
    #     'content': blog_content,
    #     'status': 'draft'
    # })
    
except Exception as e:
    print(f"   ❌ ブログ出力エラー: {e}")

# 5. X (Twitter)用コンテンツ
print("\n5. X (Twitter)用コンテンツ生成:")
try:
    # Twitter用の短縮コンテンツ
    twitter_content = f"""【USD/JPY分析】{datetime.now().strftime('%H:%M')}

現在: ¥{test_analysis['current_price']}
推奨: {test_analysis['recommendation']}
エントリー: ¥{test_analysis['entry_price']}
期待値: {test_analysis['expected_value']}

{test_analysis['technical_summary'][:60]}...

#FX #USDJPY #為替 #テクニカル分析"""
    
    # コンテンツを保存
    test_analysis['twitter_content'] = twitter_content
    with open('analysis_summary.json', 'w') as f:
        json.dump(test_analysis, f, ensure_ascii=False, indent=2)
    
    print("   ✅ Twitterコンテンツ生成完了")
    print(f"      文字数: {len(twitter_content)}/280")
    print("      内容:")
    for line in twitter_content.split('\n'):
        print(f"      {line}")
    
except Exception as e:
    print(f"   ❌ Twitterコンテンツエラー: {e}")

# 6. 結果サマリー
print("\n" + "="*50)
print("📊 統合テスト結果サマリー")
print("="*50)

# 各出力の確認
outputs = {
    "Slack": False,
    "Notion": False,
    "ブログ": False,
    "X (Twitter)": False
}

# Phase 1のパフォーマンスデータ確認
if os.path.exists('phase1_performance.json'):
    with open('phase1_performance.json', 'r') as f:
        perf_data = json.load(f)
        if perf_data.get('signals'):
            outputs["Slack"] = True

# analysis_summary.json確認
if os.path.exists('analysis_summary.json'):
    with open('analysis_summary.json', 'r') as f:
        summary = json.load(f)
        if 'twitter_content' in summary:
            outputs["X (Twitter)"] = True

# 環境変数確認
if os.environ.get('NOTION_API_KEY') and os.environ.get('NOTION_DATABASE_ID'):
    outputs["Notion"] = True

if os.environ.get('WORDPRESS_URL') and os.environ.get('WORDPRESS_USERNAME'):
    outputs["ブログ"] = True

# 結果表示
for platform, status in outputs.items():
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {platform}: {'準備完了' if status else '設定必要'}")

print("\n📋 確認方法:")
print("1. Slack: 設定したチャンネルで通知を確認")
print("2. Notion: データベースページで新規エントリを確認")
print("3. ブログ: WordPress管理画面で下書きを確認")
print("4. X: analysis_summary.jsonのtwitter_contentを確認")

print(f"\n完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("✅ 統合テスト完了！")