#!/usr/bin/env python3
"""
Phase 1: 本番環境実行スクリプト
実際のFX分析システムと統合して、定時実行に対応
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
import os

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
load_dotenv('.env')
load_dotenv('.env.phase1')  # Phase 1固有の設定を上書き

# 環境変数の一時的な修正（コメント問題の回避）
if os.getenv("BLOG_POST_HOUR", "").endswith("# 投稿する分析の時間（JST）"):
    os.environ["BLOG_POST_HOUR"] = "8"

from src.phase1_integration import Phase1FXAnalysisWithAlerts


async def main():
    """本番環境でのメイン実行"""
    
    # 現在時刻を取得
    now = datetime.now()
    current_hour = now.hour
    
    print(f"=== Phase 1 本番実行 ===")
    print(f"実行時刻: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"")
    
    # 実行時刻チェック（8:00, 15:00, 21:00）
    scheduled_hours = [8, 15, 21]
    
    if current_hour not in scheduled_hours:
        print(f"現在時刻 {current_hour}:00 は実行時刻ではありません")
        print(f"実行時刻: {', '.join(f'{h}:00' for h in scheduled_hours)}")
        
        # 強制実行オプション
        if len(sys.argv) > 1 and sys.argv[1] == '--force':
            print("\n--force オプションにより強制実行します")
        else:
            print("\n強制実行する場合: python run_phase1_production.py --force")
            return
    
    # Phase 1システムを初期化
    try:
        system = Phase1FXAnalysisWithAlerts()
        print("✅ システム初期化完了")
    except Exception as e:
        print(f"❌ システム初期化エラー: {e}")
        return
    
    # USD/JPYの分析とアラート送信
    print(f"\nUSD/JPY分析を開始します...")
    
    try:
        result = await system.analyze_and_alert("USD/JPY")
        
        if result:
            print("\n✅ 分析完了")
            
            # 結果サマリー
            if result.get('signal'):
                signal = result['signal']
                print(f"\n=== シグナル情報 ===")
                print(f"アクション: {signal['action']}")
                print(f"信頼度: {signal['confidence']:.1%}")
                
                if signal['action'] != 'NONE':
                    print(f"エントリー: {signal['entry_price']}")
                    print(f"損切り: {signal['stop_loss']}")
                    print(f"利確: {signal['take_profit']}")
                    
                    if result.get('alert'):
                        print(f"\n✅ Slackアラート送信済み")
                        print(f"記録ID: {result.get('record_id', 'N/A')}")
                else:
                    print("\n様子見 - 明確なシグナルなし")
            
            # Notion保存の確認
            if result.get('notion_url'):
                print(f"\n✅ Notion保存済み: {result['notion_url']}")
                
        else:
            print("\n❌ 分析に失敗しました")
            
    except Exception as e:
        print(f"\n❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 実行完了 ===")


if __name__ == "__main__":
    # イベントループを実行
    asyncio.run(main())