#!/usr/bin/env python3
"""
Phase 1: テスト実行スクリプト
"""
import subprocess
import sys
import os
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_unit_tests():
    """単体テストを実行"""
    print("=== Phase 1 単体テストを実行 ===\n")
    
    # pytestがインストールされているか確認
    try:
        import pytest
    except ImportError:
        print("pytestがインストールされていません。インストールします...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
    
    # テストを実行
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_phase1_alert_system.py",
        "-v",
        "--tb=short"
    ], cwd=project_root)
    
    return result.returncode == 0

def run_integration_test():
    """統合テストを実行（モックモード）"""
    print("\n=== Phase 1 統合テストを実行 ===\n")
    
    # 環境変数を設定してテストモードで実行
    env = os.environ.copy()
    env['TEST_MODE'] = '1'
    env['PYTHONPATH'] = str(project_root)
    
    # ダミーの環境変数を設定（実際の通知は送信しない）
    env['SLACK_WEBHOOK_URL'] = 'https://hooks.slack.com/services/TEST/TEST/TEST'
    env['SENDER_EMAIL'] = ''  # メール送信を無効化
    
    result = subprocess.run([
        sys.executable,
        "src/phase1_integration.py"
    ], cwd=project_root, env=env)
    
    return result.returncode == 0

def check_dependencies():
    """必要な依存関係をチェック"""
    print("=== 依存関係をチェック ===\n")
    
    required_packages = [
        'requests',
        'boto3',
        'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n不足しているパッケージ: {', '.join(missing)}")
        print("以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """メイン実行関数"""
    print("Phase 1: アラートシステムのテストを開始します\n")
    
    # 依存関係チェック
    if not check_dependencies():
        print("\n❌ 依存関係チェックに失敗しました")
        sys.exit(1)
    
    # 単体テスト実行
    if not run_unit_tests():
        print("\n❌ 単体テストに失敗しました")
        sys.exit(1)
    
    print("\n✅ 単体テストに成功しました")
    
    # 統合テスト実行
    print("\n統合テストを実行しますか？（既存のFX分析システムが必要です）")
    response = input("実行する場合は 'y' を入力: ")
    
    if response.lower() == 'y':
        if not run_integration_test():
            print("\n❌ 統合テストに失敗しました")
            sys.exit(1)
        print("\n✅ 統合テストに成功しました")
    
    print("\n🎉 Phase 1のテストが完了しました！")
    print("\n次のステップ:")
    print("1. .env.phase1 ファイルを作成して環境変数を設定")
    print("2. Slack Webhookを設定（doc/phase1_setup_guide.md参照）")
    print("3. 本番環境で実行: python src/phase1_integration.py")

if __name__ == "__main__":
    main()