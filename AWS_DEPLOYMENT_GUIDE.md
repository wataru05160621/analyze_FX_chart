# AWS定時実行セットアップガイド

## 概要
AWS EventBridge + Lambda + ECS Fargateを使用して、FX分析を定時実行します。

### スケジュール
- **平日8時（JST）**: ブログ、X、Notion投稿
- **平日15時（JST）**: Notion投稿のみ（ロンドンセッション）
- **平日21時（JST）**: Notion投稿のみ（NYセッション）

## アーキテクチャ

```
EventBridge (cron) → Lambda → ECS Fargate → 各プラットフォーム
                                    ↓
                                   S3 (チャート保存)
```

## セットアップ手順

### 1. 前提条件

```bash
# AWS CLI設定
aws configure

# 必要な権限
# - ECR: リポジトリ作成、イメージプッシュ
# - ECS: クラスター作成、タスク実行
# - Lambda: 関数作成
# - EventBridge: ルール作成
# - CloudFormation: スタック作成
# - Secrets Manager: シークレット作成
# - S3: バケット作成
```

### 2. シークレット設定

```bash
# Claude API Key
aws secretsmanager create-secret \
    --name fx-analysis/claude-api-key \
    --secret-string '{"api_key":"YOUR_CLAUDE_API_KEY"}'

# WordPress認証情報
aws secretsmanager create-secret \
    --name fx-analysis/wordpress-credentials \
    --secret-string '{
        "url":"https://by-price-action.com",
        "username":"YOUR_USERNAME",
        "password":"YOUR_PASSWORD"
    }'

# Twitter認証情報
aws secretsmanager create-secret \
    --name fx-analysis/twitter-credentials \
    --secret-string '{
        "api_key":"YOUR_API_KEY",
        "api_secret":"YOUR_API_SECRET",
        "access_token":"YOUR_ACCESS_TOKEN",
        "access_token_secret":"YOUR_ACCESS_TOKEN_SECRET"
    }'

# Notion API Key
aws secretsmanager create-secret \
    --name fx-analysis/notion-api-key \
    --secret-string '{"api_key":"YOUR_NOTION_API_KEY"}'
```

### 3. Parameter Store設定

```bash
# Notion Database ID
aws ssm put-parameter \
    --name /fx-analysis/notion-database-id \
    --value "YOUR_NOTION_DATABASE_ID" \
    --type String

# Slack Webhook URL
aws ssm put-parameter \
    --name /fx-analysis/slack-webhook-url \
    --value "YOUR_SLACK_WEBHOOK_URL" \
    --type String
```

### 4. デプロイ実行

```bash
# 環境変数設定
export SLACK_WEBHOOK_URL="YOUR_SLACK_WEBHOOK_URL"

# デプロイスクリプト実行
cd /Users/shinzato/programing/claude_code/analyze_FX_chart
chmod +x aws/deploy.sh
./aws/deploy.sh
```

### 5. 手動デプロイ（オプション）

```bash
# ECRリポジトリ作成
aws ecr create-repository --repository-name fx-analysis

# Dockerイメージビルド
docker build -f Dockerfile.aws -t fx-analysis:latest .

# ECRにプッシュ
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker tag fx-analysis:latest $ECR_URI/fx-analysis:latest
docker push $ECR_URI/fx-analysis:latest

# CloudFormationデプロイ
aws cloudformation create-stack \
    --stack-name fx-analysis-stack \
    --template-body file://aws/cloudformation-fx-analysis.yaml \
    --parameters ParameterKey=DockerImageUri,ParameterValue=$ECR_URI/fx-analysis:latest \
    --capabilities CAPABILITY_IAM
```

## テスト実行

### Lambda関数の手動実行

```bash
# 8時相当（フル投稿）
aws lambda invoke \
    --function-name fx-analysis-scheduler \
    --payload '{
        "execution_type": "full",
        "session_name": "アジアセッション"
    }' \
    output.json

# 15時相当（Notionのみ）
aws lambda invoke \
    --function-name fx-analysis-scheduler \
    --payload '{
        "execution_type": "notion_only",
        "session_name": "ロンドンセッション"
    }' \
    output.json
```

### ECSタスクの直接実行

```bash
aws ecs run-task \
    --cluster fx-analysis-cluster \
    --task-definition fx-analysis-task \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[subnet-xxx,subnet-yyy],
        securityGroups=[sg-xxx],
        assignPublicIp=ENABLED
    }"
```

## モニタリング

### CloudWatch Logs

```bash
# ECSタスクログ
aws logs tail /ecs/fx-analysis --follow

# Lambda関数ログ
aws logs tail /aws/lambda/fx-analysis-scheduler --follow
```

### EventBridgeルール確認

```bash
# ルール一覧
aws events list-rules --name-prefix fx-analysis

# ルール詳細
aws events describe-rule --name fx-analysis-8am
```

### ECSタスク状態確認

```bash
# 実行中のタスク
aws ecs list-tasks --cluster fx-analysis-cluster

# タスク詳細
aws ecs describe-tasks \
    --cluster fx-analysis-cluster \
    --tasks [TASK_ARN]
```

## コスト見積もり

月間コスト（東京リージョン）:
- **ECS Fargate**: 約$10-15（1日3回×30日）
- **Lambda**: 約$0.01（ほぼ無料）
- **EventBridge**: 無料
- **S3**: 約$1（画像保存）
- **Secrets Manager**: 約$3（5シークレット）
- **合計**: 約$15-20/月

## トラブルシューティング

### ECSタスクが失敗する
1. CloudWatch Logsでエラー確認
2. タスクロールの権限確認
3. シークレットへのアクセス権限確認

### スケジュールが実行されない
1. EventBridgeルールが有効か確認
2. Lambda関数の権限確認
3. タイムゾーン設定確認（UTC→JST変換）

### APIエラー
1. Secrets Managerの値が正しいか確認
2. API制限に達していないか確認
3. ネットワーク設定確認

## クリーンアップ

```bash
# CloudFormationスタック削除
aws cloudformation delete-stack --stack-name fx-analysis-stack

# ECRリポジトリ削除
aws ecr delete-repository --repository-name fx-analysis --force

# シークレット削除
aws secretsmanager delete-secret --secret-id fx-analysis/claude-api-key
# 他のシークレットも同様に削除
```