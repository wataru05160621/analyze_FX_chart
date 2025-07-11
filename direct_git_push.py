#!/usr/bin/env python3
import os
import subprocess

# ディレクトリ移動
os.chdir("/Users/shinzato/programing/claude_code/analyze_FX_chart")

# Gitコマンドを直接実行
commands = [
    ["git", "add", "-A"],
    ["git", "status", "--short"],
    ["git", "commit", "-m", """feat: Phase1自動デモトレーダーシステムの完全実装

- AWS ECS Fargate対応の24/7自動トレードシステム
- CloudFormationによるインフラ自動構築
- S3/DynamoDBを使用したクラウドネイティブ実装
- 自動ヘルスチェックと再起動機能
- Slack/Email通知機能
- MT4連携とWebhook対応
- ローカルテストスクリプト
- デプロイ自動化スクリプト

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""],
    ["git", "push", "origin", "main"]
]

for cmd in commands:
    print(f"実行: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"エラー: {result.stderr}")
    except Exception as e:
        print(f"例外: {e}")

print("\n処理完了")