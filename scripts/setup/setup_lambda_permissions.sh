#!/bin/bash

# Lambda関数に必要な権限を設定

echo "=== Lambda権限設定 ==="

# 1. EventBridge用のLambda実行権限を追加
echo "1. EventBridge → Lambda実行権限を設定..."
aws lambda add-permission \
  --function-name phase1-signal-verification-prod-verifySignal \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "arn:aws:events:ap-northeast-1:455931011903:rule/*" \
  2>/dev/null || echo "  (既に設定済みの可能性があります)"

# 2. S3バケットのCORS設定
echo "2. S3バケットのCORS設定..."
cat > cors-config.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": []
    }
  ]
}
EOF

aws s3api put-bucket-cors \
  --bucket fx-analysis-performance-prod-455931011903 \
  --cors-configuration file://cors-config.json \
  2>/dev/null || echo "  (S3バケットが存在しない場合は後で作成されます)"

rm cors-config.json

# 3. 環境変数をエクスポート
echo "3. 環境変数を設定..."
export SLACK_WEBHOOK_URL=$(grep SLACK_WEBHOOK_URL .env.phase1 | cut -d'=' -f2)

echo
echo "=== 権限設定完了 ==="
echo
echo "Slack Webhook URLが設定されました"
echo "Lambda関数をデプロイする準備ができました"