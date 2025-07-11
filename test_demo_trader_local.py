#!/usr/bin/env python3
"""
Phase1 デモトレーダー ローカルテストスクリプト
AWSにデプロイする前にローカルで動作確認
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def load_env_file(env_file='.env'):
    """環境変数ファイルを読み込み"""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value

async def test_demo_trader():
    """デモトレーダーのローカルテスト"""
    print("=== Phase1 デモトレーダー ローカルテスト ===")
    
    # 環境変数読み込み
    load_env_file('.env')
    load_env_file('.env.phase1')
    
    # 必要なモジュールのインポート
    try:
        from src.phase1_demo_trader import Phase1DemoTrader
        from src.chart_generator import ChartGenerator
        from src.claude_analyzer import ClaudeAnalyzer
        print("✅ モジュールインポート成功")
    except Exception as e:
        print(f"❌ モジュールインポートエラー: {e}")
        return
    
    # 環境変数確認
    env_check = {
        'ALPHA_VANTAGE_API_KEY': os.environ.get('ALPHA_VANTAGE_API_KEY'),
        'CLAUDE_API_KEY': os.environ.get('CLAUDE_API_KEY'),
        'SLACK_WEBHOOK_URL': os.environ.get('SLACK_WEBHOOK_URL'),
        'NOTIFICATION_EMAIL': os.environ.get('NOTIFICATION_EMAIL')
    }
    
    print("\n環境変数の確認:")
    for key, value in env_check.items():
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {key}: {masked_value}")
        else:
            print(f"⚠️  {key}: 未設定")
    
    # デモトレーダー初期化
    print("\n1. デモトレーダー初期化...")
    try:
        trader = Phase1DemoTrader()
        print("✅ 初期化成功")
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return
    
    # 市場分析テスト（1回だけ実行）
    print("\n2. 市場分析テスト...")
    try:
        setup = await trader.analyze_current_market()
        if setup:
            print("✅ セットアップ検出:")
            print(f"   - タイプ: {setup.get('setup_type', 'なし')}")
            print(f"   - 品質: {'⭐' * setup.get('signal_quality', 0)}")
            print(f"   - 信頼度: {setup.get('confidence', 0):.0%}")
            print(f"   - エントリー価格: {setup.get('entry_price', 'なし')}")
            
            # エントリー判断
            if trader.should_enter_trade(setup):
                print("\n3. トレードエントリーテスト...")
                trade_id = await trader.enter_trade(setup)
                if trade_id:
                    print(f"✅ エントリー成功: {trade_id}")
                else:
                    print("❌ エントリー失敗")
            else:
                print("\n⚠️  エントリー条件を満たしていません")
        else:
            print("⚠️  現在有効なセットアップはありません")
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # データベース確認
    print("\n4. データベース確認...")
    try:
        from src.phase1_data_collector import Phase1DataCollector
        collector = Phase1DataCollector()
        
        # 最近のトレード取得
        recent_trades = collector.get_recent_trades(limit=5)
        if recent_trades:
            print(f"✅ 最近のトレード: {len(recent_trades)}件")
            for trade in recent_trades[:3]:
                print(f"   - {trade['trade_id']}: {trade['pips_result']} pips")
        else:
            print("⚠️  トレード履歴なし")
        
        # パフォーマンスサマリー
        today = datetime.now().strftime('%Y-%m-%d')
        summary = collector.get_performance_summary(today, today)
        if summary:
            print(f"\n本日のパフォーマンス:")
            print(f"   - トレード数: {summary.get('total_trades', 0)}")
            print(f"   - 勝率: {summary.get('win_rate', 0):.1%}")
            print(f"   - 合計pips: {summary.get('total_pips', 0):.1f}")
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
    
    print("\n✅ ローカルテスト完了")
    print("\nAWSデプロイの準備ができました。")
    print("実行: python aws/quick-deploy-demo-trader.py")

async def test_continuous_trading():
    """連続トレードテスト（5分間）"""
    print("\n=== 連続トレードテスト（5分間） ===")
    print("Ctrl+Cで停止")
    
    # 環境変数読み込み
    load_env_file('.env')
    load_env_file('.env.phase1')
    
    from src.phase1_demo_trader import Phase1DemoTrader
    
    trader = Phase1DemoTrader()
    
    # 5分間だけテスト実行
    test_duration = 300  # 5分
    start_time = datetime.now()
    
    try:
        while (datetime.now() - start_time).total_seconds() < test_duration:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 分析実行...")
            
            setup = await trader.analyze_current_market()
            if setup and trader.should_enter_trade(setup):
                trade_id = await trader.enter_trade(setup)
                if trade_id:
                    print(f"✅ 新規トレード: {trade_id}")
            
            await trader.monitor_active_trades()
            
            # 30秒待機（テスト用に短縮）
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nテスト終了")

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 引数でモード選択
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        asyncio.run(test_continuous_trading())
    else:
        asyncio.run(test_demo_trader())