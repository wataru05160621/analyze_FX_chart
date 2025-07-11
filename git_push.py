#!/usr/bin/env python3
"""GitHubへのプッシュスクリプト"""
import subprocess
import sys

def run_git_command(cmd):
    """Gitコマンドを実行"""
    print(f"実行: git {cmd}")
    result = subprocess.run(f"git {cmd}", shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"エラー: {result.stderr}")
    return result.returncode == 0

# コマンド実行
commands = [
    "add -A",
    "status --short",
    'commit -m "feat: Phase1自動デモトレーダーシステムの完全実装\n\n- AWS ECS Fargate対応の24/7自動トレードシステム\n- CloudFormationによるインフラ自動構築\n- S3/DynamoDBを使用したクラウドネイティブ実装\n- 自動ヘルスチェックと再起動機能\n- Slack/Email通知機能\n- MT4連携とWebhook対応\n- ローカルテストスクリプト\n- デプロイ自動化スクリプト\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"',
    "push origin main"
]

for cmd in commands:
    if not run_git_command(cmd):
        print(f"コマンド失敗: git {cmd}")
        sys.exit(1)

print("\n✅ GitHubへのプッシュが完了しました！")