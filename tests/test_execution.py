#!/usr/bin/env python3
import subprocess
import sys
import os

# 実行ディレクトリを設定
os.chdir('/Users/shinzato/programing/claude_code/analyze_FX_chart')

print("=== スクリプト実行テスト ===\n")

# 1. Slack通知
print("1. Slack通知テスト:")
try:
    result = subprocess.run(
        [sys.executable, 'post_slack.py'],
        capture_output=True,
        text=True,
        timeout=30
    )
    print(result.stdout)
    if result.stderr:
        print("エラー:", result.stderr)
except Exception as e:
    print(f"実行エラー: {e}")

print("\n" + "-"*50 + "\n")

# 2. WordPress投稿
print("2. WordPress投稿テスト:")
try:
    result = subprocess.run(
        [sys.executable, 'post_wp.py'],
        capture_output=True,
        text=True,
        timeout=30
    )
    print(result.stdout)
    if result.stderr:
        print("エラー:", result.stderr)
except Exception as e:
    print(f"実行エラー: {e}")

print("\n完了！各プラットフォームで結果を確認してください。")