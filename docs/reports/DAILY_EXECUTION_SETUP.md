# 日次実行セットアップ完了

## 実装内容

### 1. 検証日数表示機能
すべての投稿に「検証○日目」が自動的に表示されます。

#### 各プラットフォームでの表示例
- **WordPress**: `【USD/JPY】2024年3月15日 朝の相場分析 - 検証15日目`
- **X/Twitter**: `#検証15日目`
- **Notion**: `分析日時: 2024年3月15日 14:30 - 検証15日目`
- **Slack**: `*FX分析完了 (Volmanメソッド) - 検証15日目*`

### 2. AWS Lambda実装
`aws_lambda_function.py` に検証日数機能を統合：
- 実行時に検証日数を自動計算
- フェーズ情報（Phase1/2/3）も表示
- エラー時のSlack通知機能

### 3. デプロイ手順

#### 必要な環境変数の設定
```bash
# .envファイルから読み込む場合
source .env
source .env.phase1

# または手動で設定
export CLAUDE_API_KEY="your_claude_api_key"
export WORDPRESS_URL="https://by-price-action.com"
export WORDPRESS_USERNAME="your_username"
export WORDPRESS_PASSWORD="your_password"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx"
```

#### デプロイ実行
```bash
# 実行権限を付与
chmod +x aws/deploy-with-verification.sh

# デプロイ実行
./aws/deploy-with-verification.sh
```

### 4. 実行スケジュール

AWS EventBridgeによる自動実行：
- **8:00 JST**: 全プラットフォーム投稿（WordPress, X, Notion, Slack）
- **15:00 JST**: Notionのみ投稿
- **21:00 JST**: Notionのみ投稿

### 5. 動作確認

#### CloudWatch Logsでリアルタイムログ確認
```bash
aws logs tail /aws/lambda/fx-analysis-function --follow --region ap-northeast-1
```

#### 手動実行テスト
```bash
# AWS Consoleから
AWS Lambda > fx-analysis-function > Test

# CLIから
aws lambda invoke \
  --function-name fx-analysis-function \
  --region ap-northeast-1 \
  output.json
```

### 6. コスト見積もり

月額コスト（概算）：
- Lambda: $2-3（1日3回実行）
- S3: $1（チャート画像保存）
- Secrets Manager: $1（APIキー管理）
- CloudWatch: $1（ログ保存）
- **合計: 約$5-6/月**

### 7. 検証日数の管理

#### 開始日の確認
```bash
# S3から開始日ファイルをダウンロード
aws s3 cp s3://fx-analysis-charts-{ACCOUNT_ID}/phase1_start_date.json .
cat phase1_start_date.json
```

#### 開始日のリセット（必要な場合）
```bash
echo '{"start_date":"2024-03-01T00:00:00","phase":"Phase1","description":"FXスキャルピング検証プロジェクト"}' > phase1_start_date.json
aws s3 cp phase1_start_date.json s3://fx-analysis-charts-{ACCOUNT_ID}/phase1_start_date.json
```

### 8. トラブルシューティング

#### Lambda実行エラー
1. CloudWatch Logsを確認
2. 環境変数が正しく設定されているか確認
3. IAMロールの権限を確認

#### 投稿が失敗する場合
1. API認証情報を確認（Secrets Manager）
2. 各プラットフォームのAPI制限を確認
3. ネットワーク接続を確認

### 9. 今後の拡張予定

- 検証結果の自動集計（週次・月次レポート）
- Phase移行時の自動通知
- 成績グラフの自動生成
- AIによる改善提案機能

## 完了状態

✅ 検証日数トラッカー実装
✅ 全プラットフォームへの検証日数表示
✅ AWS Lambda関数の更新
✅ デプロイスクリプトの作成
✅ 日次自動実行の設定

**すべての準備が完了しました。デプロイを実行してください。**