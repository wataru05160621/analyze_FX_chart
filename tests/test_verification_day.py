#!/usr/bin/env python3
"""
検証日数機能のテストスクリプト
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def test_verification_tracker():
    """検証日数トラッカーのテスト"""
    from src.verification_tracker import VerificationTracker, get_tracker
    
    print("=== 検証日数トラッカーテスト ===\n")
    
    # 1. 新規トラッカー作成（テスト用）
    test_tracker = VerificationTracker("test_phase1_start_date.json")
    
    # 2. 現在の検証日数
    current_day = test_tracker.get_verification_day()
    print(f"現在の検証日数: {current_day}日目")
    print(f"表示テキスト: {test_tracker.get_verification_text()}")
    
    # 3. 進捗状況
    progress = test_tracker.get_progress_percentage()
    print(f"\nPhase1進捗: {progress:.1f}%")
    
    # 4. フェーズ情報
    phase_info = test_tracker.get_phase_info()
    print(f"\n現在のフェーズ: {phase_info['current_phase']}")
    print(f"フェーズ説明: {phase_info['description']}")
    print(f"開始日: {phase_info['start_date']}")
    
    # 5. 過去の日付でテスト
    print("\n--- 過去の日付でシミュレーション ---")
    past_date = datetime.now() - timedelta(days=30)
    test_tracker.reset_start_date(past_date)
    print(f"30日前開始: {test_tracker.get_verification_text()}")
    
    # 6. Phase2シミュレーション
    phase2_date = datetime.now() - timedelta(days=100)
    test_tracker.reset_start_date(phase2_date)
    phase_info = test_tracker.get_phase_info()
    print(f"\n100日前開始: {test_tracker.get_verification_text()}")
    print(f"フェーズ: {phase_info['current_phase']} - {phase_info['description']}")
    
    # クリーンアップ
    if Path("test_phase1_start_date.json").exists():
        Path("test_phase1_start_date.json").unlink()
    
    print("\n✅ テスト完了")

def test_posting_with_verification():
    """投稿での検証日数表示テスト"""
    print("\n=== 投稿での検証日数表示テスト ===\n")
    
    from src.verification_tracker import get_tracker
    from src.blog_publisher import BlogPublisher
    
    # トラッカー初期化
    tracker = get_tracker()
    verification_day = tracker.get_verification_text()
    
    # サンプル分析
    sample_analysis = """
現在価格：150.500円

## 相場状況
- EMA配列：25EMA > 75EMA > 200EMA（上昇配列）
- ビルドアップ：三角保ち合い形成中
- セットアップ：パターンブレイク待ち

## トレード判断
エントリー候補：150.700円のブレイクアウト
"""
    
    # 1. ブログタイトル
    today = datetime.now().strftime("%Y年%m月%d日")
    blog_title = f"【USD/JPY】{today} 朝の相場分析 - {verification_day}"
    print(f"ブログタイトル: {blog_title}")
    
    # 2. Twitterテキスト
    twitter_text = f"""【{datetime.now().strftime('%m/%d')} USD/JPY チャート解説】
USD/JPY: 150.500円
📈EMA上昇配列
📊ビルドアップ形成中

Volmanスキャルピングメソッドに基づく教育的解説

#USDJPY #ドル円 #FX学習 #{verification_day}"""
    
    print(f"\nTwitter投稿:")
    print(twitter_text)
    
    # 3. Slack通知
    slack_message = f"""*FX分析完了 (Volmanメソッド) - {verification_day}*
時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}
通貨ペア: USD/JPY

{sample_analysis[:200]}..."""
    
    print(f"\nSlack通知:")
    print(slack_message)
    
    # 4. Notion
    notion_content = f"分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')} - {verification_day}"
    print(f"\nNotion表示: {notion_content}")

if __name__ == "__main__":
    # 環境変数読み込み
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value
    
    # テスト実行
    test_verification_tracker()
    test_posting_with_verification()
    
    print("\n=== 実際の投稿で表示される内容 ===")
    from src.verification_tracker import get_tracker
    tracker = get_tracker()
    print(f"検証日数: {tracker.get_verification_text()}")
    print(f"進捗: {tracker.get_progress_percentage():.1f}%")
    print("\n各プラットフォームで上記の検証日数が表示されます。")