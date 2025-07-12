#!/usr/bin/env python
"""
実際の価格を使用した検証テスト
"""
import os
import sys
import time
import json
from datetime import datetime

# 環境変数を読み込み
def load_env():
    with open('.env.phase1', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

load_env()

# 環境変数の確認
print("=== 環境変数の確認 ===")
api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
print(f"ALPHA_VANTAGE_API_KEY: {api_key[:8] if api_key else 'Not set'}...")

# 価格取得テスト
from src.local_signal_verifier import LocalSignalVerifier

verifier = LocalSignalVerifier()

print("\n=== 実価格取得テスト ===")

# USD/JPYの実価格を取得
currency_pairs = ['USDJPY', 'USD/JPY']

for pair in currency_pairs:
    print(f"\n{pair}の価格を取得中...")
    price = verifier.get_current_price(pair)
    print(f"  取得価格: {price}")

# 新しいテストシグナルで実価格検証
print("\n=== 実価格での検証テスト ===")

from src.phase1_performance_automation import Phase1PerformanceAutomation

# 現在の実価格を基準にシグナルを作成
current_price = verifier.get_current_price('USDJPY')
print(f"現在のUSD/JPY: {current_price}")

# 実価格に近いシグナルを作成
test_signal = {
    "action": "BUY",
    "entry_price": current_price - 0.10,  # 現在価格より10銭安く
    "stop_loss": current_price - 0.40,    # 40銭の損切り
    "take_profit": current_price + 0.30,  # 30銭の利確
    "confidence": 0.80
}

print(f"\nテストシグナル:")
print(f"  エントリー: {test_signal['entry_price']:.2f}")
print(f"  損切り: {test_signal['stop_loss']:.2f}")
print(f"  利確: {test_signal['take_profit']:.2f}")

# 短時間で検証
os.environ['VERIFY_AFTER_HOURS'] = '0.001'  # 3.6秒後

performance = Phase1PerformanceAutomation()
signal_id = performance.record_signal(test_signal, {
    "summary": "実価格テスト: リアルタイムレートでの検証",
    "currency_pair": "USDJPY"
})

print(f"\n✅ シグナル記録: {signal_id}")
print("⏳ 5秒後に実価格で検証...")

time.sleep(5)

# 手動で検証実行
verifier.run_once()

# 結果を確認
with open('phase1_performance.json', 'r') as f:
    data = json.load(f)

result = next((s for s in data['signals'] if s['id'] == signal_id), None)

if result and result.get('verified_at'):
    print(f"\n📊 検証結果:")
    print(f"  ステータス: {result['status']}")
    print(f"  結果: {result['result']}")
    print(f"  エグジット価格: {result['actual_exit']}")
    print(f"  損益: {result['pnl']:.2f} pips")
    print(f"  損益率: {result['pnl_percentage']:.3f}%")
    
    # 実価格で検証されたことを確認
    if result['actual_exit'] == current_price:
        print("\n✅ 実際の価格で検証されました！")
    else:
        print(f"\n⚠️ エグジット価格が異なります")
        print(f"  期待値: {current_price}")
        print(f"  実際値: {result['actual_exit']}")

# 検証システムを再起動
print("\n=== 検証システムの再起動 ===")
import subprocess

log_file = "logs/verification_daemon.log"
with open(log_file, 'a') as f:
    process = subprocess.Popen(
        [sys.executable, 'src/local_signal_verifier.py'],
        stdout=f,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

if process.poll() is None:
    print(f"✅ 検証システムを再起動しました (PID: {process.pid})")
    with open('.verification_daemon.pid', 'w') as f:
        f.write(str(process.pid))
else:
    print("❌ 再起動に失敗しました")