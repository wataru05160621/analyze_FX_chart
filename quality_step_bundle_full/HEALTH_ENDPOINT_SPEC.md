# HEALTH_ENDPOINT_SPEC.md

## 返却項目
- last_success_ts
- last_run_id
- error_counts (by module)
- queue/backlog（任意）

## 実装例
- CloudWatch Logs Insights または DynamoDB に直近成功RunIdを保存。
- Slack `/fx status` からも呼べるように Lambda + API Gateway で簡易実装。
