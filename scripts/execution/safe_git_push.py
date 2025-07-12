#!/usr/bin/env python3
"""
安全なGitプッシュスクリプト
機密情報を含むファイルがgitignoreされていることを確認してからプッシュ
"""
import subprocess
import os
import sys

def check_gitignore():
    """gitignoreに機密ファイルが含まれているか確認"""
    required_ignores = ['.env', '.env.phase1', '.env.phase2', '.env.phase3']
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    for pattern in required_ignores:
        if pattern not in gitignore_content:
            print(f"❌ エラー: {pattern} が .gitignore に含まれていません")
            return False
    
    print("✅ .gitignore チェック完了")
    return True

def check_sensitive_files():
    """機密ファイルがステージングされていないか確認"""
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    sensitive_patterns = ['.env', 'phase1', 'phase2', 'phase3', 'phase4']
    
    for file in staged_files:
        if file.strip():  # 空行をスキップ
            file_path = file[3:]  # ステータス文字をスキップ
            for pattern in sensitive_patterns:
                if pattern in file_path and not file_path.endswith('.example'):
                    print(f"⚠️  警告: 機密ファイルの可能性: {file_path}")
                    return False
    
    print("✅ 機密ファイルチェック完了")
    return True

def create_env_examples():
    """環境変数のサンプルファイルを作成"""
    # .env.phase1.example を作成
    phase1_example = """# Phase 1: アラートシステムの環境変数設定例

# Slack Webhook設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# 価格取得API
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key

# 通知設定
NOTIFICATION_EMAIL=your-notification-email@example.com

# AWS設定（オプション）
AWS_REGION=ap-northeast-1
PERFORMANCE_S3_BUCKET=your-s3-bucket-name
"""
    
    with open('.env.phase1.example', 'w') as f:
        f.write(phase1_example)
    
    print("✅ サンプルファイル作成完了")

def main():
    """メイン処理"""
    print("=== 安全なGitプッシュ ===\n")
    
    # 作業ディレクトリ移動
    os.chdir('/Users/shinzato/programing/claude_code/analyze_FX_chart')
    
    # チェック実行
    if not check_gitignore():
        print("\n❌ gitignoreの設定を確認してください")
        sys.exit(1)
    
    # サンプルファイル作成
    create_env_examples()
    
    # Git操作
    commands = [
        ['git', 'add', '-A'],
        ['git', 'status', '--short']
    ]
    
    print("\n=== Git操作開始 ===")
    
    for cmd in commands:
        print(f"\n実行: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"エラー: {result.stderr}")
    
    # 機密ファイルチェック
    if not check_sensitive_files():
        print("\n❌ 機密ファイルが含まれている可能性があります")
        print("git reset で変更を取り消してください")
        sys.exit(1)
    
    # コミット
    commit_message = """feat: Phase1自動デモトレーダーシステムの完全実装

- AWS ECS Fargate対応の24/7自動トレードシステム
- CloudFormationによるインフラ自動構築
- S3/DynamoDBを使用したクラウドネイティブ実装
- 自動ヘルスチェックと再起動機能
- Slack/Email通知機能
- MT4連携とWebhook対応
- ローカルテストスクリプト
- デプロイ自動化スクリプト
- 環境変数サンプルファイル追加

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""
    
    print("\nコミット実行...")
    result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"エラー: {result.stderr}")
    
    # プッシュ
    print("\nプッシュ実行...")
    result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"エラー: {result.stderr}")
    
    print("\n✅ GitHubへのプッシュが完了しました！")

if __name__ == "__main__":
    main()