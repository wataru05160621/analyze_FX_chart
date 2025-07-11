# Phase1 デモトレーダー デプロイガイド

## 環境変数について

既に`.env`と`.env.phase1`に必要な環境変数が設定されています：

### 既に設定済みの環境変数
- ✅ **CLAUDE_API_KEY**: `.env`に設定済み
- ✅ **SLACK_WEBHOOK_URL**: `.env.phase1`に設定済み
- ✅ **ALPHA_VANTAGE_API_KEY**: `.env.phase1`に設定済み
- ✅ **AWS_REGION**: `.env`と`.env.phase1`に設定済み（ap-northeast-1）

### 追加で必要な設定
**必須ではありませんが、以下はオプションです：**
- **NOTIFICATION_EMAIL**: トレード通知を受け取るメールアドレス（オプション）

## デプロイ手順

### 1. AWS CLIの設定確認
```bash
# AWS CLIがインストールされているか確認
aws --version

# AWSアカウントにログインしているか確認
aws sts get-caller-identity
```

### 2. デプロイ実行
```bash
# クイックデプロイスクリプトを実行（.envファイルを自動読み込み）
python aws/quick-deploy-demo-trader.py
```

これだけです！スクリプトが自動的に：
- .envと.env.phase1ファイルを読み込み
- Dockerイメージをビルドしてプッシュ
- CloudFormationスタックをデプロイ
- ECSサービスを起動

### 3. デプロイ後の確認
```bash
# ログの確認
aws logs tail /ecs/phase1-demo-trader --follow --region ap-northeast-1

# トレード記録の確認
aws dynamodb scan --table-name phase1-trades --region ap-northeast-1

# サービス状態の確認
aws ecs describe-services \
  --cluster phase1-demo-trader-cluster \
  --services phase1-demo-trader-service \
  --region ap-northeast-1
```

## Slack通知の例
デモトレードが実行されると、以下のような通知がSlackに送信されます：

```
🟢 デモトレード結果
ID: DEMO_20240315_143022
セットアップ: A
結果: 20.0 pips (TP)
品質: ⭐⭐⭐⭐
保有時間: 35分
```

## トラブルシューティング

### エラー: Docker not found
```bash
# Dockerをインストール
brew install --cask docker  # Mac
# または https://docs.docker.com/get-docker/ からダウンロード
```

### エラー: AWS CLI not configured
```bash
# AWS CLIを設定
aws configure
# Access Key ID、Secret Access Key、Region（ap-northeast-1）を入力
```

### エラー: ECS service not starting
```bash
# ログを確認
aws logs tail /ecs/phase1-demo-trader --since 10m --region ap-northeast-1

# タスク定義を確認
aws ecs describe-task-definition --task-definition phase1-demo-trader
```

## コスト管理
- 月額コスト: 約$25-35
- Fargate Spotを使用して70%削減可能
- 不要になったら必ず削除：
  ```bash
  aws cloudformation delete-stack --stack-name phase1-demo-trader
  ```

## 次のステップ
1. 3ヶ月間データを収集
2. DynamoDBのデータをエクスポートして分析
3. Phase 2のブログ戦略に活用
4. Phase 3のAIシグナルサービスへ発展