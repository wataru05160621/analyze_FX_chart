#!/usr/bin/env python
"""
出力テストを実行
"""
import subprocess
import sys
import os

# 環境変数を設定
env = os.environ.copy()
env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

# テストスクリプトを実行
result = subprocess.run(
    [sys.executable, 'test_all_outputs.py'],
    env=env,
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("エラー出力:")
    print(result.stderr)