# Phase1 デモトレーダー AWS デプロイメントガイド

## 概要
このガイドでは、Phase1自動デモトレードシステムをAWS上に24時間365日稼働させる手順を説明します。

## アーキテクチャ
```
ECS Fargate (24/7稼働)
  ↓
S3 (チャート保存) + DynamoDB (トレード記録)
  ↓
SNS (通知) → Email/Slack
  ↓
CloudWatch (監視) → Lambda (自動再起動)
```

## 前提条件
- AWS CLIがインストール済み
- Dockerがインストール済み
- AWS アカウントとIAM権限
- ECR リポジトリへのアクセス権限

## デプロイ手順

### 1. Dockerイメージのビルドとプッシュ

```bash
# ECRリポジトリの作成
aws ecr create-repository --repository-name phase1-demo-trader

# ログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.ap-northeast-1.amazonaws.com

# イメージのビルド
docker build -f aws/Dockerfile.demo-trader -t phase1-demo-trader .

# タグ付け
docker tag phase1-demo-trader:latest [ACCOUNT_ID].dkr.ecr.ap-northeast-1.amazonaws.com/phase1-demo-trader:latest

# プッシュ
docker push [ACCOUNT_ID].dkr.ecr.ap-northeast-1.amazonaws.com/phase1-demo-trader:latest
```

### 2. CloudFormationスタックのデプロイ

```bash
# パラメータファイルの作成
cat > demo-trader-params.json << EOF
[
  {
    "ParameterKey": "ImageUri",
    "ParameterValue": "[ACCOUNT_ID].dkr.ecr.ap-northeast-1.amazonaws.com/phase1-demo-trader:latest"
  },
  {
    "ParameterKey": "VpcId",
    "ParameterValue": "vpc-xxxxxxxxx"
  },
  {
    "ParameterKey": "SubnetIds",
    "ParameterValue": "subnet-xxx,subnet-yyy"
  },
  {
    "ParameterKey": "AlphaVantageApiKey",
    "ParameterValue": "YOUR_API_KEY"
  },
  {
    "ParameterKey": "ClaudeApiKey",
    "ParameterValue": "YOUR_CLAUDE_KEY"
  },
  {
    "ParameterKey": "SlackWebhookUrl",
    "ParameterValue": "https://hooks.slack.com/services/xxx"
  },
  {
    "ParameterKey": "NotificationEmail",
    "ParameterValue": "your-email@example.com"
  }
]
EOF

# スタックのデプロイ
aws cloudformation create-stack \
  --stack-name phase1-demo-trader \
  --template-body file://aws/cloudformation-demo-trader.yaml \
  --parameters file://demo-trader-params.json \
  --capabilities CAPABILITY_IAM
```

### 3. デプロイの確認

```bash
# スタックのステータス確認
aws cloudformation describe-stacks --stack-name phase1-demo-trader

# ECSサービスの確認
aws ecs describe-services \
  --cluster phase1-demo-trader-cluster \
  --services phase1-demo-trader-service

# ログの確認
aws logs tail /ecs/phase1-demo-trader --follow
```

## 運用管理

### ログの確認
```bash
# CloudWatch Logsでリアルタイムログを確認
aws logs tail /ecs/phase1-demo-trader --follow --since 1h
```

### トレード履歴の確認
```bash
# DynamoDBから最新のトレードを取得
aws dynamodb query \
  --table-name phase1-trades \
  --index-name status-index \
  --key-condition-expression "#s = :status" \
  --expression-attribute-names '{"#s": "status"}' \
  --expression-attribute-values '{":status": {"S": "active"}}' \
  --limit 10
```

### サービスの手動再起動
```bash
# サービスの再起動
aws ecs update-service \
  --cluster phase1-demo-trader-cluster \
  --service phase1-demo-trader-service \
  --force-new-deployment
```

### スケーリング調整
```bash
# タスク数の変更（通常は1で十分）
aws ecs update-service \
  --cluster phase1-demo-trader-cluster \
  --service phase1-demo-trader-service \
  --desired-count 1
```

## モニタリング

### CloudWatchダッシュボード
自動的に以下のメトリクスが収集されます：
- ECSタスクのCPU/メモリ使用率
- DynamoDBの読み書きキャパシティ
- S3のリクエスト数
- Lambda実行回数

### アラート
以下の場合に通知が送信されます：
- タスクが停止した場合
- エラーが連続して発生した場合
- 新規トレードが実行された場合

## コスト見積もり

月額コスト（概算）：
- ECS Fargate: $15-20（512MB/0.25vCPU）
- DynamoDB: $5-10（オンデマンド）
- S3: $1-2（チャート保存）
- CloudWatch: $1-2
- **合計: 約$25-35/月**

※ Fargate Spotを使用することで、さらに70%程度のコスト削減が可能

## トラブルシューティング

### タスクが起動しない
```bash
# タスク定義の確認
aws ecs describe-task-definition --task-definition phase1-demo-trader

# 失敗したタスクのログ確認
aws ecs describe-tasks \
  --cluster phase1-demo-trader-cluster \
  --tasks [TASK_ARN]
```

### API制限エラー
- Claude APIの制限に達した場合、自動的にリトライされます
- 必要に応じてタスク定義の環境変数でAPI_RETRY_DELAYを調整

### DynamoDBスロットリング
- 読み書きキャパシティを増やすか、オンデマンドモードに変更
```bash
aws dynamodb update-table \
  --table-name phase1-trades \
  --billing-mode PAY_PER_REQUEST
```

## 削除手順

```bash
# CloudFormationスタックの削除
aws cloudformation delete-stack --stack-name phase1-demo-trader

# ECRイメージの削除
aws ecr delete-repository --repository-name phase1-demo-trader --force

# S3バケットの削除（データも削除される）
aws s3 rm s3://fx-analysis-phase1-[ACCOUNT_ID] --recursive
aws s3 rb s3://fx-analysis-phase1-[ACCOUNT_ID]
```

## セキュリティベストプラクティス

1. **APIキーの管理**
   - AWS Secrets Managerを使用してAPIキーを保存
   - 環境変数ではなくSecretsから取得

2. **ネットワーク**
   - プライベートサブネットでの実行を推奨
   - NAT Gatewayを経由した外部通信

3. **監査**
   - CloudTrailでAPI呼び出しを記録
   - VPCフローログを有効化

## 次のステップ

1. **データ分析**
   - 3ヶ月後にDynamoDBのデータをエクスポート
   - Amazon Athenaでクエリ分析

2. **機械学習**
   - SageMakerでモデル構築
   - Phase 3のAIシグナルサービスへ移行

3. **スケーリング**
   - 複数通貨ペアへの拡張
   - リージョン間レプリケーション