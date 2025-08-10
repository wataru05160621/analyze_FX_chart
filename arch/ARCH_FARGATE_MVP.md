# ARCH_FARGATE_MVP

- EventBridge Scheduler → **ECS Fargate RunTask**
- Network: subnets ['subnet-06fba36a849bb6647', 'subnet-02aef8bf85b9ceb0d'] / SG sg-03cb601e40f6e32ac / AssignPublicIp=ENABLED
- Secrets: NOTION_API_KEY / NOTION_DB_ID / SLACK_WEBHOOK_URL / S3_BUCKET / TWELVEDATA_API_KEY
- Outputs: Notion page (+ two chart images) / Slack message / S3 (2 PNG + JSON)
- Data: TwelveData time_series (5min & 1h), symbol=USD/JPY
