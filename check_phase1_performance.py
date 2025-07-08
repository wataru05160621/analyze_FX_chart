#!/usr/bin/env python3
"""
Phase 1: パフォーマンス記録確認スクリプト
記録されたシグナルの統計情報を表示
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from collections import defaultdict

# プロジェクトルートをPATHに追加
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv('.env.phase1')

from src.phase1_alert_system import PerformanceTracker


def display_performance_stats():
    """パフォーマンス統計を表示"""
    
    tracker = PerformanceTracker()
    
    print("=== Phase 1 パフォーマンス統計 ===")
    print(f"確認日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # ローカルストレージから記録を読み込み（テスト用）
    # 本番環境ではDynamoDBから読み込む
    records = []
    
    # _recordsが存在する場合（インメモリストレージ）
    if hasattr(tracker, '_records'):
        records = list(tracker._records.values())
    
    if not records:
        print("記録されたシグナルがありません")
        print("\nシグナルを記録するには:")
        print("1. python run_phase1_demo_simple.py を実行")
        print("2. python run_phase1_production.py --force を実行")
        return
    
    # 統計情報を計算
    total_signals = len(records)
    buy_signals = sum(1 for r in records if r.get('signal', {}).get('action') == 'BUY')
    sell_signals = sum(1 for r in records if r.get('signal', {}).get('action') == 'SELL')
    none_signals = sum(1 for r in records if r.get('signal', {}).get('action') == 'NONE')
    
    print(f"【シグナル統計】")
    print(f"総シグナル数: {total_signals}")
    print(f"  買いシグナル: {buy_signals}")
    print(f"  売りシグナル: {sell_signals}")
    print(f"  様子見: {none_signals}")
    
    # 時間別統計
    hourly_stats = defaultdict(int)
    for record in records:
        timestamp = datetime.fromisoformat(record['timestamp'])
        hourly_stats[timestamp.hour] += 1
    
    if hourly_stats:
        print(f"\n【時間別シグナル】")
        for hour in sorted(hourly_stats.keys()):
            print(f"  {hour:02d}:00 - {hourly_stats[hour]}件")
    
    # 最近のシグナル
    print(f"\n【最近のシグナル（最新5件）】")
    sorted_records = sorted(records, key=lambda x: x['timestamp'], reverse=True)
    
    for i, record in enumerate(sorted_records[:5]):
        timestamp = datetime.fromisoformat(record['timestamp'])
        signal = record.get('signal', {})
        
        print(f"\n{i+1}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   アクション: {signal.get('action', 'N/A')}")
        print(f"   信頼度: {signal.get('confidence', 0):.1%}")
        
        if signal.get('action') not in ['NONE', None]:
            print(f"   エントリー: {signal.get('entry_price', 0)}")
            print(f"   損切り: {signal.get('stop_loss', 0)}")
            print(f"   利確: {signal.get('take_profit', 0)}")
    
    # 信頼度分析
    confidences = [r.get('signal', {}).get('confidence', 0) for r in records if r.get('signal', {}).get('action') != 'NONE']
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        print(f"\n【信頼度分析】")
        print(f"平均信頼度: {avg_confidence:.1%}")
        print(f"最高信頼度: {max(confidences):.1%}")
        print(f"最低信頼度: {min(confidences):.1%}")


def export_to_csv():
    """記録をCSVファイルにエクスポート"""
    tracker = PerformanceTracker()
    
    if not hasattr(tracker, '_records') or not tracker._records:
        print("エクスポートする記録がありません")
        return
    
    # CSVファイル作成
    csv_path = Path(f"phase1_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    with open(csv_path, 'w') as f:
        # ヘッダー
        f.write("Timestamp,Action,Entry,StopLoss,TakeProfit,Confidence\n")
        
        # データ
        for record in tracker._records.values():
            signal = record.get('signal', {})
            f.write(f"{record['timestamp']},")
            f.write(f"{signal.get('action', '')},")
            f.write(f"{signal.get('entry_price', '')},")
            f.write(f"{signal.get('stop_loss', '')},")
            f.write(f"{signal.get('take_profit', '')},")
            f.write(f"{signal.get('confidence', '')}\n")
    
    print(f"\n✅ CSVファイルを作成しました: {csv_path}")


def main():
    """メイン実行"""
    display_performance_stats()
    
    # CSVエクスポートオプション
    if len(sys.argv) > 1 and sys.argv[1] == '--export':
        export_to_csv()


if __name__ == "__main__":
    main()