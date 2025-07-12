# AWS Lambda & S3 セットアップガイド

FX分析システムをAWS環境で自動実行するためのセットアップガイドです。

## 前提条件

1. **AWSアカウント**
2. **AWS CLI** がインストール・設定済み
3. **適切なIAM権限**

## 必要なAWS権限

以下の権限を持つIAMユーザーまたはロールが必要です：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:*",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:PassRole",
                "s3:CreateBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:PutBucketPolicy",
                "events:PutRule",
                "events:PutTargets",
                "cloudformation:*",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

## セットアップ手順

### 1. AWS CLIの設定

```bash
# AWS CLIのインストール (macOS)
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# 認証情報の設定
aws configure
```

入力する情報：
- AWS Access Key ID
- AWS Secret Access Key
- Default region name: `ap-northeast-1`
- Default output format: `json`

### 2. 環境変数の設定

```bash
# 必要な環境変数をエクスポート
export OPENAI_API_KEY="your_openai_api_key"
export NOTION_API_KEY="your_notion_api_key"
export NOTION_DATABASE_ID="your_notion_database_id"
export TRADINGVIEW_CUSTOM_URL="your_tradingview_chart_url"
```

### 3. デプロイ方法の選択

#### 方法A: SAM (推奨)

```bash
# SAM CLIのインストール
brew install aws/tap/aws-sam-cli

# デプロイ
chmod +x deploy.sh
./deploy.sh dev sam
```

#### 方法B: Serverless Framework

```bash
# Serverless CLIのインストール
npm install -g serverless

# デプロイ
./deploy.sh dev serverless
```

## S3バケットの設定

### 自動作成

デプロイスクリプト実行時に自動的に以下のバケットが作成されます：

- `fx-analyzer-images-{environment}`: チャート画像保存用
- `fx-analyzer-deploy-{environment}`: デプロイパッケージ用

### 手動作成（オプション）

```bash
# S3バケットの作成
aws s3 mb s3://fx-analyzer-images-prod --region ap-northeast-1

# パブリックアクセスブロックの設定
aws s3api put-public-access-block \
    --bucket fx-analyzer-images-prod \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

## Lambda関数の設定

### 環境変数

Lambda関数には以下の環境変数が自動設定されます：

| 変数名 | 説明 |
|--------|------|
| `OPENAI_API_KEY` | OpenAI API キー |
| `NOTION_API_KEY` | Notion API キー |
| `NOTION_DATABASE_ID` | Notion データベース ID |
| `AWS_S3_BUCKET` | S3 バケット名 |
| `TRADINGVIEW_CUSTOM_URL` | Trading View チャート URL |
| `USE_WEB_CHATGPT` | false (Lambda環境ではAPI使用) |

### スケジュール設定

以下のスケジュールで自動実行されます：

- **8:00 AM JST** (UTC 23:00): `cron(0 23 * * ? *)`
- **3:00 PM JST** (UTC 6:00): `cron(0 6 * * ? *)`
- **9:00 PM JST** (UTC 12:00): `cron(0 12 * * ? *)`

## テスト実行

### 1. Lambda関数の手動実行

```bash
# テスト関数の実行
aws lambda invoke \
    --function-name fx-analyzer-test-dev \
    --payload file://test-event.json \
    response.json

# 結果の確認
cat response.json
```

### 2. ローカルテスト（SAM）

```bash
# ローカルでLambda関数を実行
sam local invoke TestFunction --event test-event.json
```

### 3. ログの確認

```bash
# CloudWatch Logsの確認
aws logs tail /aws/lambda/fx-analyzer-dev --follow

# 特定の時間範囲でログを確認
aws logs filter-log-events \
    --log-group-name /aws/lambda/fx-analyzer-dev \
    --start-time $(date -d '1 hour ago' +%s)000
```

## 監視とアラート

### CloudWatch メトリクス

以下のメトリクスを監視することを推奨：

- **Duration**: 実行時間
- **Errors**: エラー数
- **Throttles**: スロットリング回数
- **Invocations**: 実行回数

### CloudWatch アラームの設定

```bash
# エラー数のアラーム
aws cloudwatch put-metric-alarm \
    --alarm-name "fx-analyzer-errors" \
    --alarm-description "FX Analyzer Lambda errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --dimensions Name=FunctionName,Value=fx-analyzer-prod \
    --evaluation-periods 1
```

## コスト最適化

### Lambda実行時間の最適化

- **メモリサイズ**: 2048MB（Playwright実行のため）
- **タイムアウト**: 900秒（15分）
- **実行回数**: 1日3回

### S3ストレージの管理

- **ライフサイクルポリシー**: 30日後に自動削除
- **バージョニング**: 有効（誤削除防止）

## トラブルシューティング

### 一般的な問題

1. **権限エラー**
   ```
   解決: IAM権限を確認し、必要な権限を追加
   ```

2. **タイムアウトエラー**
   ```
   解決: Lambda関数のタイムアウト設定を確認（現在15分）
   ```

3. **メモリ不足**
   ```
   解決: メモリサイズを増加（Playwright用に2048MB推奨）
   ```

4. **Playwright実行エラー**
   ```
   解決: 
   - Lambda Layer の設定確認
   - 依存関係の確認
   - ヘッドレスブラウザの設定確認
   ```

### ログの詳細確認

```bash
# エラーログのフィルタリング
aws logs filter-log-events \
    --log-group-name /aws/lambda/fx-analyzer-prod \
    --filter-pattern "ERROR"

# 特定の実行のログ確認
aws logs get-log-events \
    --log-group-name /aws/lambda/fx-analyzer-prod \
    --log-stream-name "$(aws logs describe-log-streams \
        --log-group-name /aws/lambda/fx-analyzer-prod \
        --order-by LastEventTime --descending \
        --limit 1 --query 'logStreams[0].logStreamName' \
        --output text)"
```

## アップデート手順

### コードの更新

```bash
# 1. コードを修正
# 2. 再デプロイ
./deploy.sh prod sam

# 3. テスト実行
aws lambda invoke \
    --function-name fx-analyzer-test-prod \
    response.json
```

### 設定の更新

環境変数やスケジュール設定を変更する場合：

1. `template.yaml` または `serverless.yml` を編集
2. 再デプロイを実行

## セキュリティベストプラクティス

1. **最小権限の原則**: 必要最小限のIAM権限のみ付与
2. **APIキーの管理**: AWS Secrets Manager の使用を検討
3. **VPC設定**: 必要に応じてプライベートサブネット内で実行
4. **ログの監視**: 異常なアクセスパターンの監視

## 費用見積もり

月間コスト（1日3回実行の場合）：

- **Lambda実行**: 約$5-10
- **S3ストレージ**: 約$1-2  
- **CloudWatch Logs**: 約$1-3
- **データ転送**: 約$1-2

**合計**: 約$8-17/月