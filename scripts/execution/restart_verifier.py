#!/usr/bin/env python
"""
検証デーモンを再起動
"""
import os
import subprocess
import sys
import time

# 既存のプロセスを停止
if os.path.exists('.verification_daemon.pid'):
    with open('.verification_daemon.pid', 'r') as f:
        old_pid = f.read().strip()
    try:
        os.kill(int(old_pid), 15)  # SIGTERM
        print(f"既存のプロセス (PID: {old_pid}) を停止しました")
        time.sleep(1)
    except:
        pass

# 新しいプロセスを起動
log_file = "logs/verification_daemon.log"
with open(log_file, 'a') as f:
    f.write(f"\n\n=== 再起動: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    process = subprocess.Popen(
        [sys.executable, 'src/local_signal_verifier.py'],
        stdout=f,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

if process.poll() is None:
    print(f"✅ 検証デーモンを起動しました (PID: {process.pid})")
    with open('.verification_daemon.pid', 'w') as f:
        f.write(str(process.pid))
    
    # 環境変数の確認
    print("\n環境変数の確認:")
    import sys
    sys.path.insert(0, '.')
    from src.local_signal_verifier import LocalSignalVerifier
    
    verifier = LocalSignalVerifier()
    
    # 実価格を取得してテスト
    print("\n実価格取得テスト:")
    price = verifier.get_current_price('USDJPY')
    print(f"USD/JPY: {price}")
    
    # APIキーの確認
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if api_key and api_key != 'demo':
        print(f"\n✅ Alpha Vantage APIキー設定済み: {api_key[:8]}...")
        print("✅ 実際の価格を使用します")
    else:
        print("\n⚠️ デモ価格モードです")
else:
    print("❌ 起動に失敗しました")