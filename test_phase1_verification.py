#!/usr/bin/env python
"""
Phase 1検証システムのテスト
"""
import json
from datetime import datetime, timedelta
from src.phase1_performance_automation import Phase1PerformanceAutomation

# テスト用のシグナルを作成
test_signal = {
    "action": "BUY",
    "entry_price": 145.50,
    "stop_loss": 145.20,
    "take_profit": 146.00,
    "confidence": 0.85
}

test_analysis = {
    "summary": "テスト分析: USD/JPYは上昇トレンド",
    "currency_pair": "USDJPY"
}

print("=== Phase 1 検証システムテスト ===")
print()

# パフォーマンス記録システムを初期化
performance = Phase1PerformanceAutomation()

# シグナルを記録（これにより24時間後の検証が自動スケジュールされます）
signal_id = performance.record_signal(test_signal, test_analysis)

print(f"\n✅ テストシグナルを記録しました: {signal_id}")

# 現在のパフォーマンスデータを表示
with open('phase1_performance.json', 'r') as f:
    data = json.load(f)
    print(f"\n現在の記録シグナル数: {len(data['signals'])}")

# 検証キューを確認
try:
    with open('verification_queue.json', 'r') as f:
        queue = json.load(f)
        print(f"検証待ちシグナル数: {len(queue)}")
        
        if queue:
            next_verification = queue[-1]
            print(f"\n次の検証:")
            print(f"  シグナルID: {next_verification['signal_id']}")
            print(f"  検証予定時刻: {next_verification['verify_at']}")
except FileNotFoundError:
    print("検証キューファイルがまだ作成されていません")

print("\n💡 ヒント:")
print("- 通常は24時間後に自動検証されます")
print("- テストのため、.env.phase1で VERIFY_AFTER_HOURS=0.01 に設定すると36秒後に検証されます")
print("- python src/local_signal_verifier.py で検証システムを起動できます")