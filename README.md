# FX Analysis Automation System v2

AWS ECS Fargate上で動作する自動FX分析システム。TwelveData APIからデータを取得し、品質ゲートを適用した分析を実行、Notion/Slack/S3へ結果を出力します。

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with credentials
- Docker installed (for local development)
- Python 3.13+ (for local development)
- jq installed (for scripts)

### Environment Variables

```bash
# Non-secrets (configured in task definition)
APP_NAME=analyze-fx
TZ=Asia/Tokyo
PAIR=USDJPY
SYMBOL=USD/JPY
TIMEFRAMES=5m,1h
S3_PREFIX=charts
LOG_LEVEL=INFO
DATA_SOURCE=twelvedata

# Secrets (stored in AWS Secrets Manager)
NOTION_API_KEY=<stored in secrets manager>
NOTION_DB_ID=<stored in secrets manager>
SLACK_WEBHOOK_URL=<stored in secrets manager>
S3_BUCKET=<stored in secrets manager>
TWELVEDATA_API_KEY=<stored in secrets manager>
```

## 📋 Deployment Steps

### 1. Initial Setup

```bash
# Clone repository
git clone git@github.com:wataru05160621/analyze_FX_chart.git
cd analyze_FX_chart

# Make scripts executable
chmod +x scripts/*.sh
```

### 2. Deploy Infrastructure

```bash
# Apply S3 lifecycle policies
./scripts/apply_s3_lifecycle.sh

# Deploy EventBridge schedulers
./scripts/deploy_scheduler.sh      # Main analysis (08:00 JST weekdays)
./scripts/deploy_daily_stats.sh     # Daily stats (23:45 JST)
```

### 3. Build and Push Docker Image

```bash
# Build for x86_64 (Fargate)
docker build --platform linux/amd64 -t analyze-fx .

# Tag and push to ECR
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com
docker tag analyze-fx:latest 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/analyze-fx:latest
docker push 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/analyze-fx:latest
```

### 4. Run Smoke Test

```bash
# Dry run (test mode)
./scripts/run_once.sh dryrun

# Production run (after successful dry run)
./scripts/run_once.sh production
```

## 🏗️ Architecture

```
EventBridge Scheduler
    ↓
ECS Fargate Task
    ↓
┌─────────────────────────────┐
│  FX Analysis System v2      │
├─────────────────────────────┤
│  • Quality Gates            │
│  • 6 Setup Patterns (A-F)   │
│  • Beta+EWMA EV Calculation │
│  • Linguistic Guard         │
└─────────────────────────────┘
    ↓           ↓          ↓
  Notion      Slack       S3
```

### Components

- **EventBridge Scheduler**: Triggers analysis at 08:00 JST weekdays
- **ECS Fargate**: Serverless container execution
- **Secrets Manager**: Secure credential storage
- **S3**: Chart images and JSON results storage
- **Notion**: Analysis documentation with 17 properties
- **Slack**: Real-time notifications

## 📊 Schedules

| Job | Schedule | Description |
|-----|----------|-------------|
| Main Analysis | 08:00 JST weekdays | FX market analysis with v2 engine |
| Daily Stats | 23:45 JST daily | Calculate win rates and update stats |

## 🔧 Operations Runbook

### Check System Status

```bash
# View running tasks
aws ecs list-tasks --cluster analyze-fx-cluster --region ap-northeast-1

# Check scheduler status
aws scheduler list-schedules --region ap-northeast-1 --query 'Schedules[?contains(Name, `fx`)]' --output table

# View recent logs
aws logs tail /ecs/analyze-fx --follow --region ap-northeast-1
```

### Manual Execution

```bash
# Run analysis manually
./scripts/run_once.sh production

# Run daily stats manually
aws ecs run-task \
    --cluster analyze-fx-cluster \
    --task-definition analyze-fx-daily-stats \
    --launch-type FARGATE \
    --network-configuration '{
        "awsvpcConfiguration": {
            "subnets": ["subnet-06fba36a849bb6647", "subnet-02aef8bf85b9ceb0d"],
            "securityGroups": ["sg-03cb601e40f6e32ac"],
            "assignPublicIp": "ENABLED"
        }
    }' \
    --region ap-northeast-1
```

### Troubleshooting

#### Task Fails to Start

1. Check task definition:
```bash
aws ecs describe-task-definition --task-definition analyze-fx --region ap-northeast-1
```

2. Verify IAM roles:
```bash
aws iam get-role --role-name ecsTaskExecutionRole
```

3. Check subnet availability:
```bash
aws ec2 describe-subnets --subnet-ids subnet-06fba36a849bb6647 subnet-02aef8bf85b9ceb0d --region ap-northeast-1
```

#### Analysis Errors

1. Check CloudWatch logs:
```bash
aws logs get-log-events \
    --log-group-name /ecs/analyze-fx \
    --log-stream-name <stream-name> \
    --region ap-northeast-1
```

2. Verify Secrets Manager access:
```bash
aws secretsmanager get-secret-value --secret-id analyze-fx/notion-api-key --region ap-northeast-1
```

3. Test TwelveData API:
```bash
curl "https://api.twelvedata.com/time_series?symbol=USD/JPY&interval=5min&apikey=<key>"
```

#### Notion/Slack Issues

1. Test Notion connection:
```python
from notion_client import Client
client = Client(auth="<api-key>")
client.databases.query(database_id="<db-id>")
```

2. Test Slack webhook:
```bash
curl -X POST <webhook-url> -H 'Content-Type: application/json' -d '{"text":"Test message"}'
```

### Rollback Procedure

```bash
# Disable schedulers
aws scheduler update-schedule --name analyze-fx-prod-0800-jst --state DISABLED --region ap-northeast-1
aws scheduler update-schedule --name analyze-fx-dailystats-2345-jst --state DISABLED --region ap-northeast-1

# Revert to previous task definition
aws ecs update-service \
    --cluster analyze-fx-cluster \
    --service analyze-fx \
    --task-definition analyze-fx:<previous-revision> \
    --region ap-northeast-1
```

## 📈 Monitoring

### CloudWatch Metrics

- Task success/failure rate
- Execution duration
- Memory/CPU utilization
- API call counts

### Alarms

```bash
# Create alarm for task failures
aws cloudwatch put-metric-alarm \
    --alarm-name fx-analysis-failures \
    --alarm-description "Alert on FX analysis task failures" \
    --metric-name FailedTaskCount \
    --namespace ECS/ContainerInsights \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1
```

## 🔐 Security

- All secrets stored in AWS Secrets Manager
- Network isolation with security groups (egress only)
- IAM roles with least privilege
- Encrypted S3 bucket
- No hardcoded credentials

## 📝 Acceptance Criteria

✅ Analysis runs at 08:00 JST weekdays only (30-min schedule disabled)  
✅ Notion pages always include 2 chart images (5m/1h)  
✅ Features JSON block at end of every Notion page  
✅ Slack notifications use Block Kit templates  
✅ S3 lifecycle policies applied (30d Glacier, 90d delete for charts)  
✅ Daily stats job runs at 23:45 JST  
✅ Schema validation passes for all outputs  
✅ Linguistic guard removes investment advice language  

## 🚦 Health Checks

```bash
# Check last successful run
aws s3 ls s3://analyze-fx-455931011903-apne1/results/ --recursive | tail -1

# Verify Notion page creation
curl -X POST https://api.notion.com/v1/databases/<db-id>/query \
    -H "Authorization: Bearer <api-key>" \
    -H "Notion-Version: 2022-06-28" \
    -H "Content-Type: application/json" \
    -d '{"sorts":[{"property":"Date","direction":"descending"}],"page_size":1}'
```

## 📚 Documentation

- [Quality Step Bundle](quality_step_bundle_full/README.md)
- [Analysis Specification](quality_step_bundle_full/docs/ANALYSIS_SPEC.md)  
- [Notion Contract v2](quality_step_bundle_full/notion/NOTION_CONTRACT_v2.md)
- [Daily Stats Job](quality_step_bundle_full/jobs/DAILY_STATS_JOB.md)
- [Schema Definition](quality_step_bundle_full/schema/analysis_output.schema.json)

## 🤝 Support

For issues or questions:
1. Check CloudWatch logs
2. Review this runbook
3. Contact the development team

---
Version: 2.0.0  
Last Updated: 2024-12-11