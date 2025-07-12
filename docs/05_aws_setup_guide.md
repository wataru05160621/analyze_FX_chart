# AWS Lambda デプロイガイド

## 必要な準備

### 1. AWS CLI設定
```bash
# AWS CLIインストール
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# 認証情報設定
aws configure
```

### 2. SAM CLI設定
```bash
# Homebrewでインストール（macOS）
brew tap aws/tap
brew install aws-sam-cli

# 設定確認
sam --version
```

### 3. 環境変数設定
```bash
# .envファイルを作成/更新
export OPENAI_API_KEY="sk-proj-your-key"
export CLAUDE_API_KEY="sk-ant-your-key"
export NOTION_API_KEY="ntn_your-key"
export NOTION_DATABASE_ID="your-database-id"
export ALERT_EMAIL="your-email@example.com"
```

## デプロイ手順

### 1. 自動デプロイ
```bash
# デプロイスクリプト実行
./deploy.sh

# または環境を指定
ENVIRONMENT=prod ./deploy.sh
```

### 2. 手動デプロイ
```bash
# SAMビルド
sam build

# SAMデプロイ
sam deploy \
    --stack-name fx-analyzer-prod \
    --s3-bucket fx-analyzer-deploy-YOUR-ACCOUNT-ID-ap-northeast-1 \
    --capabilities CAPABILITY_IAM \
    --region ap-northeast-1 \
    --parameter-overrides \
        Environment=prod \
        AlertEmail=your-email@example.com \
    --confirm-changeset
```

## デプロイ後の設定

### 1. Secrets Manager設定
```bash
aws secretsmanager put-secret-value \
    --secret-id fx-analyzer-secrets-prod \
    --secret-string '{
        "OPENAI_API_KEY": "sk-proj-your-openai-key",
        "CLAUDE_API_KEY": "sk-ant-your-claude-key",
        "NOTION_API_KEY": "ntn_your-notion-key",
        "NOTION_DATABASE_ID": "your-notion-database-id",
        "ANALYSIS_MODE": "claude",
        "USE_WEB_CHATGPT": "false"
    }'
```

### 2. SNSサブスクリプション確認
- デプロイ後にメールが送信されます
- メール内の確認リンクをクリックしてサブスクリプションを有効化

### 3. テスト実行
```bash
# Lambda関数の手動実行
aws lambda invoke \
    --function-name fx-analyzer-prod \
    --payload '{}' \
    response.json

# レスポンス確認
cat response.json
```

## 監視とログ

### 1. CloudWatchログ
```bash
# ログストリーム確認
aws logs describe-log-streams \
    --log-group-name /aws/lambda/fx-analyzer-prod

# ログをリアルタイム監視
aws logs tail /aws/lambda/fx-analyzer-prod --follow
```

### 2. CloudWatchメトリクス
- FXAnalyzer名前空間でカスタムメトリクスを確認
- エラー率、実行時間、成功率などを監視

### 3. アラーム設定
自動的に以下のアラームが設定されます：
- エラー率 > 50%
- 実行時間 > 10分
- Lambda関数エラー発生

## トラブルシューティング

### よくある問題

1. **権限エラー**
   ```bash
   # IAMロールに必要な権限があることを確認
   aws iam get-role --role-name fx-analyzer-prod-FXAnalyzerFunctionRole-*
   ```

2. **Secrets Manager接続エラー**
   ```bash
   # シークレットの存在確認
   aws secretsmanager describe-secret --secret-id fx-analyzer-secrets-prod
   ```

3. **Notion接続エラー**
   ```bash
   # Notion APIキーとデータベースIDを確認
   curl -H "Authorization: Bearer $NOTION_API_KEY" \
        -H "Notion-Version: 2022-06-28" \
        "https://api.notion.com/v1/databases/$NOTION_DATABASE_ID"
   ```

### ログ分析
```bash
# エラーログのフィルタリング
aws logs filter-log-events \
    --log-group-name /aws/lambda/fx-analyzer-prod \
    --filter-pattern "ERROR"

# 特定期間のログ取得
aws logs filter-log-events \
    --log-group-name /aws/lambda/fx-analyzer-prod \
    --start-time $(date -d "1 hour ago" +%s)000
```

## スケジュール設定

デプロイ後、以下のスケジュールで自動実行されます：

- **朝**: 8:00 AM JST (UTC 23:00 前日)
- **午後**: 3:00 PM JST (UTC 06:00)  
- **夜**: 9:00 PM JST (UTC 12:00)

### スケジュール変更
template.yamlのcron式を変更してre-deploy:
```yaml
Schedule: cron(0 23 * * ? *)  # JST 8:00 AM
```

## コスト最適化

### Lambda使用料金
- 実行時間: 15分（最大）
- メモリ: 1024MB
- 月3回実行 × 30日 = 90回/月
- 推定コスト: $1-2/月

### その他のサービス
- S3ストレージ: $0.1/月（画像30日保存）
- CloudWatch: $0.5/月（ログ・メトリクス）
- SNS: $0.1/月（アラート通知）

合計推定コスト: **$2-3/月**