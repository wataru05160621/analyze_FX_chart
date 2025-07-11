#!/usr/bin/env python3
"""
Phase 1のステータスと本日の実行状況を確認
"""
import os
import json
from datetime import datetime, timedelta
import subprocess

def check_phase1_enabled():
    """Phase 1が有効かチェック"""
    env_file = ".env.phase1"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
            if "ENABLE_PHASE1=true" in content:
                print("✅ Phase 1は有効になっています")
                return True
            else:
                print("❌ Phase 1は無効です（ENABLE_PHASE1=true が設定されていません）")
                return False
    else:
        print("❌ .env.phase1 ファイルが見つかりません")
        return False

def check_performance_file():
    """パフォーマンスファイルの状態を確認"""
    perf_file = "phase1_performance.json"
    if os.path.exists(perf_file):
        with open(perf_file, 'r') as f:
            data = json.load(f)
            signal_count = len(data.get('signals', []))
            last_updated = data.get('last_updated', 'なし')
            
            print(f"\n📊 パフォーマンスファイル状態:")
            print(f"  - 記録されたシグナル数: {signal_count}")
            print(f"  - 最終更新: {last_updated}")
            
            # 今日のシグナルをチェック
            today = datetime.now().strftime('%Y-%m-%d')
            today_signals = [s for s in data.get('signals', []) 
                           if s.get('timestamp', '').startswith(today)]
            
            print(f"  - 本日のシグナル: {len(today_signals)}件")
            
            if today_signals:
                for sig in today_signals:
                    print(f"    - {sig['id']}: {sig['action']} @ {sig['entry_price']}")
    else:
        print("❌ phase1_performance.json が見つかりません")

def check_ecs_execution():
    """本日のECS実行を確認"""
    print("\n🚀 ECSタスク実行状況:")
    
    # 最新のECSタスクを確認
    result = subprocess.run([
        'aws', 'ecs', 'describe-tasks',
        '--cluster', 'fx-analyzer-cluster-prod',
        '--tasks', 'arn:aws:ecs:ap-northeast-1:455931011903:task/fx-analyzer-cluster-prod/ede54646e29b4383a525a8858642757a',
        '--query', 'tasks[0].[createdAt,stoppedAt,stopCode]',
        '--output', 'json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        created = data[0]
        stopped = data[1]
        status = data[2]
        
        print(f"  - 開始時刻: {created}")
        print(f"  - 終了時刻: {stopped}")
        print(f"  - ステータス: {status}")
        
        if status == "EssentialContainerExited":
            print("  ✅ タスクは正常に完了しました")
    else:
        print("  ❌ ECS情報の取得に失敗しました")

def check_logs():
    """ログファイルを確認"""
    print("\n📝 ログファイル確認:")
    
    log_dir = "logs/"
    if os.path.exists(log_dir):
        # fx_analysis.logの最新エントリを確認
        log_file = os.path.join(log_dir, "fx_analysis.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Phase 1関連のログを探す
            phase1_logs = [l for l in lines if 'Phase 1' in l]
            
            if phase1_logs:
                print(f"  - Phase 1関連ログ: {len(phase1_logs)}件")
                print("  - 最新のPhase 1ログ:")
                for log in phase1_logs[-3:]:
                    print(f"    {log.strip()}")
            else:
                print("  - Phase 1関連のログが見つかりません")

def suggest_fixes():
    """修正案を提示"""
    print("\n💡 推奨アクション:")
    
    # Phase 1が無効の場合
    if not check_phase1_enabled():
        print("\n1. Phase 1を有効にする:")
        print("   echo 'ENABLE_PHASE1=true' >> .env.phase1")
    
    # パフォーマンスファイルがない場合
    if not os.path.exists("phase1_performance.json"):
        print("\n2. パフォーマンスファイルを初期化:")
        print("   ./setup_performance_tracking.sh")
    
    # main_multi_currency.pyの統合確認
    print("\n3. main_multi_currency.pyへの統合を確認:")
    print("   grep -n 'Phase1Integration\\|phase1_performance' src/main_multi_currency.py")
    
    print("\n4. 手動でPhase 1を実行してテスト:")
    print("   python -c \"from src.phase1_alert_system import *; print('Phase 1 modules loaded successfully')\"")

if __name__ == "__main__":
    print("=== Phase 1 ステータスチェック ===")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_phase1_enabled()
    check_performance_file()
    check_ecs_execution()
    check_logs()
    suggest_fixes()