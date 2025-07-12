#!/usr/bin/env python3
"""
品質テストを実行
"""
import subprocess
import sys
import os

# 環境変数を設定
env = os.environ.copy()
env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

# テストスクリプトを実行
print("=== 品質改善テストを実行 ===\n")

try:
    result = subprocess.run(
        [sys.executable, 'test_quality_improvement.py'],
        env=env,
        capture_output=True,
        text=True,
        check=True
    )
    
    print(result.stdout)
    
    if result.stderr:
        print("\nエラー出力:")
        print(result.stderr)
        
except subprocess.CalledProcessError as e:
    print(f"テスト実行エラー: {e}")
    print(f"stdout: {e.stdout}")
    print(f"stderr: {e.stderr}")
except Exception as e:
    print(f"予期しないエラー: {e}")