#!/bin/bash
cd /Users/shinzato/programing/claude_code/analyze_FX_chart

echo "=== Git操作開始 ==="

# 全ファイルをステージング
git add -A

# 状態確認
echo -e "\n変更ファイル:"
git status --short

# コミット
git commit -m "feat: Phase1自動デモトレーダーシステムの完全実装

- AWS ECS Fargate対応の24/7自動トレードシステム
- CloudFormationによるインフラ自動構築
- S3/DynamoDBを使用したクラウドネイティブ実装
- 自動ヘルスチェックと再起動機能
- Slack/Email通知機能
- MT4連携とWebhook対応
- ローカルテストスクリプト
- デプロイ自動化スクリプト

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# プッシュ
git push origin main

echo -e "\n✅ GitHubへのプッシュが完了しました！"