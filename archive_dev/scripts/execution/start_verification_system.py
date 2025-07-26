#!/usr/bin/env python
"""
Phase 1検証システムの起動とセットアップ
"""
import os
import sys
import subprocess
import time
import json
from datetime import datetime, timedelta

def setup_alpha_vantage():
    """Alpha Vantage APIキーを自動設定"""
    print("=== Alpha Vantage API設定 ===")
    
    # 無料のデモAPIキーを使用
    demo_api_key = "demo"
    
    # 既存の設定を確認
    env_file = ".env.phase1"
    with open(env_file, 'r') as f:
        content = f.read()
    
    if 'ALPHA_VANTAGE_API_KEY' not in content:
        # 設定を追加
        with open(env_file, 'a') as f:
            f.write(f"\n# 価格取得API（デモ版）\nALPHA_VANTAGE_API_KEY={demo_api_key}\n")
        print("✅ Alpha Vantage APIキー（デモ版）を設定しました")
    else:
        print("✅ Alpha Vantage APIキーは既に設定されています")
    
    # 環境変数に設定
    os.environ['ALPHA_VANTAGE_API_KEY'] = demo_api_key
    return demo_api_key

def start_verification_daemon():
    """検証システムをデーモンとして起動"""
    print("\n=== 検証システムの起動 ===")
    
    # 既存のプロセスを確認
    try:
        result = subprocess.run(['pgrep', '-f', 'local_signal_verifier.py'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("⚠️ 検証システムは既に実行中です")
            return False
    except:
        pass
    
    # バックグラウンドで起動
    log_file = "logs/verification_daemon.log"
    os.makedirs("logs", exist_ok=True)
    
    with open(log_file, 'w') as f:
        process = subprocess.Popen(
            [sys.executable, 'src/local_signal_verifier.py'],
            stdout=f,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    
    time.sleep(2)  # 起動を待つ
    
    # プロセスが正常に起動したか確認
    if process.poll() is None:
        print(f"✅ 検証システムを起動しました (PID: {process.pid})")
        print(f"   ログファイル: {log_file}")
        
        # PIDを保存
        with open('.verification_daemon.pid', 'w') as f:
            f.write(str(process.pid))
        
        return True
    else:
        print("❌ 検証システムの起動に失敗しました")
        return False

def test_verification_system():
    """検証システムの動作テスト"""
    print("\n=== 動作テスト ===")
    
    # テスト用にVERIFY_AFTER_HOURSを短く設定
    os.environ['VERIFY_AFTER_HOURS'] = '0.01'  # 36秒後に検証
    
    from src.phase1_performance_automation import Phase1PerformanceAutomation
    
    # テストシグナルを作成
    test_signal = {
        "action": "BUY",
        "entry_price": 145.50,
        "stop_loss": 145.20,
        "take_profit": 146.00,
        "confidence": 0.85
    }
    
    test_analysis = {
        "summary": "動作テスト: USD/JPYは上昇トレンド中",
        "currency_pair": "USDJPY"
    }
    
    # パフォーマンス記録
    performance = Phase1PerformanceAutomation()
    signal_id = performance.record_signal(test_signal, test_analysis)
    
    print(f"✅ テストシグナルを記録: {signal_id}")
    
    # 検証キューを確認
    queue_file = "verification_queue.json"
    if os.path.exists(queue_file):
        with open(queue_file, 'r') as f:
            queue = json.load(f)
        
        # 最新のエントリを確認
        latest = next((q for q in reversed(queue) if q['signal_id'] == signal_id), None)
        if latest:
            verify_time = datetime.fromisoformat(latest['verify_at'])
            wait_seconds = (verify_time - datetime.now()).total_seconds()
            print(f"✅ 検証スケジュール確認: {wait_seconds:.0f}秒後に実行予定")
            
            if wait_seconds > 0 and wait_seconds < 60:
                print(f"\n⏳ {wait_seconds:.0f}秒待機中...")
                print("（検証が実行されるとSlack通知が送信されます）")
                
                # カウントダウン表示
                for i in range(int(wait_seconds) + 5):
                    remaining = int(wait_seconds) - i
                    if remaining > 0:
                        print(f"\r残り {remaining} 秒...", end='', flush=True)
                    time.sleep(1)
                
                print("\n\n✅ 検証が実行されました！")
                
                # 結果を確認
                with open('phase1_performance.json', 'r') as f:
                    data = json.load(f)
                
                verified_signal = next((s for s in data['signals'] if s['id'] == signal_id), None)
                if verified_signal and verified_signal.get('status') == 'completed':
                    print("\n📊 検証結果:")
                    print(f"  結果: {verified_signal.get('result')}")
                    print(f"  損益: {verified_signal.get('pnl', 0):.1f} pips")
                    print(f"  検証時刻: {verified_signal.get('verified_at')}")
        else:
            print("⚠️ 検証スケジュールが見つかりません")
    else:
        print("⚠️ 検証キューファイルが作成されていません")
    
    # 環境変数を元に戻す
    os.environ['VERIFY_AFTER_HOURS'] = '24'

def show_status():
    """現在のステータスを表示"""
    print("\n=== 現在のステータス ===")
    
    # 検証デーモンの状態
    if os.path.exists('.verification_daemon.pid'):
        with open('.verification_daemon.pid', 'r') as f:
            pid = f.read().strip()
        
        try:
            # プロセスが存在するか確認
            subprocess.run(['ps', '-p', pid], check=True, capture_output=True)
            print(f"✅ 検証システム: 実行中 (PID: {pid})")
        except:
            print("❌ 検証システム: 停止中")
            os.remove('.verification_daemon.pid')
    else:
        print("❌ 検証システム: 停止中")
    
    # パフォーマンスデータ
    if os.path.exists('phase1_performance.json'):
        with open('phase1_performance.json', 'r') as f:
            data = json.load(f)
        
        total = len(data.get('signals', []))
        completed = len([s for s in data.get('signals', []) if s.get('status') == 'completed'])
        pending = total - completed
        
        print(f"\n📊 シグナル統計:")
        print(f"  総シグナル数: {total}")
        print(f"  検証完了: {completed}")
        print(f"  検証待ち: {pending}")
        
        if data.get('statistics'):
            stats = data['statistics']
            print(f"\n📈 パフォーマンス:")
            print(f"  期待値: {stats.get('expected_value_percentage', 0):.2f}%")
            print(f"  勝率: {stats.get('win_rate', 0):.1%}")
            print(f"  リスクリワード比: {stats.get('risk_reward_ratio', 0):.2f}")

def main():
    """メイン処理"""
    print("=== Phase 1 検証システム セットアップ ===")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Alpha Vantage API設定
    api_key = setup_alpha_vantage()
    
    # 2. 検証システムを起動
    if start_verification_daemon():
        # 3. 動作テスト
        test_verification_system()
    
    # 4. ステータス表示
    show_status()
    
    print("\n✅ セットアップ完了！")
    print("\n次のコマンドで確認できます:")
    print("  - ログ確認: tail -f logs/verification_daemon.log")
    print("  - プロセス確認: ps aux | grep local_signal_verifier")
    print("  - 停止: kill $(cat .verification_daemon.pid)")

if __name__ == "__main__":
    main()