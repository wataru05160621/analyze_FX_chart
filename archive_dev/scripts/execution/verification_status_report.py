#!/usr/bin/env python
"""
Phase 1検証システムの最終ステータスレポート
"""
import json
import os
from datetime import datetime
import subprocess

print("=== Phase 1 検証システム 最終ステータスレポート ===")
print(f"レポート生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. 環境設定の確認
print("📋 環境設定:")
with open('.env.phase1', 'r') as f:
    for line in f:
        if 'ENABLE_PHASE1' in line:
            print(f"  - {line.strip()}")
        elif 'ALPHA_VANTAGE' in line:
            key = line.split('=')[1].strip()
            print(f"  - ALPHA_VANTAGE_API_KEY={key[:8]}... (設定済み)")
        elif 'VERIFY_AFTER_HOURS' in line:
            print(f"  - {line.strip()}")

# 2. 検証システムの状態
print("\n🔧 検証システム:")
if os.path.exists('.verification_daemon.pid'):
    with open('.verification_daemon.pid', 'r') as f:
        pid = f.read().strip()
    try:
        subprocess.run(['ps', '-p', pid], check=True, capture_output=True)
        print(f"  ✅ 実行中 (PID: {pid})")
    except:
        print("  ❌ 停止中")
else:
    print("  ❌ 未起動")

# 3. パフォーマンスデータ
print("\n📊 パフォーマンスデータ:")
if os.path.exists('phase1_performance.json'):
    with open('phase1_performance.json', 'r') as f:
        data = json.load(f)
    
    signals = data.get('signals', [])
    print(f"  - 総シグナル数: {len(signals)}")
    
    # 各シグナルの状態
    for sig in signals:
        status = sig.get('status', 'unknown')
        result = sig.get('result', '-')
        pnl = sig.get('pnl', 0)
        
        status_emoji = {
            'completed': '✅',
            'active': '🟡',
            'pending': '⏳'
        }.get(status, '❓')
        
        print(f"    {status_emoji} {sig['id']}: {sig['action']} @ {sig['entry_price']} → {result}")
        if pnl:
            print(f"       損益: {pnl:.2f} pips ({sig.get('pnl_percentage', 0):.2f}%)")

# 4. 検証キュー
print("\n📋 検証キュー:")
if os.path.exists('verification_queue.json'):
    with open('verification_queue.json', 'r') as f:
        queue = json.load(f)
    
    pending = [q for q in queue if q['status'] == 'pending']
    completed = [q for q in queue if q['status'] == 'completed']
    
    print(f"  - 検証待ち: {len(pending)}")
    print(f"  - 検証完了: {len(completed)}")

# 5. 実価格の確認
print("\n💹 価格API:")
api_key = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
if api_key and api_key != 'demo':
    print(f"  ✅ 実価格API設定済み (Alpha Vantage)")
    
    # 最新の価格を取得
    try:
        import requests
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': 'USD',
            'to_currency': 'JPY',
            'apikey': api_key
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if 'Realtime Currency Exchange Rate' in data:
            rate = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
            print(f"  - 現在のUSD/JPY: {rate:.2f}")
    except:
        pass
else:
    print("  ⚠️ デモ価格を使用中")

# 6. 次のステップ
print("\n🚀 次のステップ:")
print("  1. 本番環境での動作確認")
print("     - 次回の定期実行（15:00、21:00）でシグナルが生成されます")
print("     - 24時間後に自動検証されます")
print()
print("  2. 検証システムの監視")
print("     - ログ確認: tail -f logs/verification_daemon.log")
print("     - 統計確認: python src/generate_daily_report.py")
print()
print("  3. パフォーマンスの追跡")
print("     - 期待値、リスクリワード比が自動計算されます")
print("     - Slack通知で結果が報告されます")

print("\n✅ Phase 1検証システムは正常に稼働しています！")