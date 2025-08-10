# FX Analysis Automation System

Automated FX market analysis system that runs on AWS ECS Fargate, analyzes market data using TwelveData API, and publishes results to Notion, Slack, and S3.

## Features

- 📊 Multi-timeframe analysis (5m, 1h)
- 📈 Technical indicators (EMA25, ATR20, Build-up patterns)
- 🎯 6 trading setup types (Pattern Break, Pullback, etc.)
- 📸 Chart generation with matplotlib
- 💾 S3 storage with pre-signed URLs
- 📝 Notion database integration with image blocks
- 💬 Slack notifications with analysis summary
- 🐳 Docker containerization for ECS Fargate

## Architecture

```
EventBridge Scheduler
    ↓
ECS Fargate Task
    ↓
┌─────────────────────────┐
│  TwelveData API         │ → Market Data
├─────────────────────────┤
│  Analysis Core          │ → Setup Detection
├─────────────────────────┤
│  Chart Generation       │ → PNG Charts
├─────────────────────────┤
│  S3 Upload              │ → Storage
├─────────────────────────┤
│  Notion Update          │ → Database
├─────────────────────────┤
│  Slack Notification     │ → Alerts
└─────────────────────────┘
```

## Setup

### Prerequisites

- Python 3.11+
- AWS Account with ECS, S3 access
- TwelveData API key
- Notion API key and database
- Slack webhook URL

### Local Development

1. Clone the repository:
```bash
git clone git@github.com:wataru05160621/analyze_FX_chart.git
cd analyze_FX_chart
```

2. Copy environment template:
```bash
cp .env.example .env
```

3. Fill in your credentials in `.env`:
```
TWELVEDATA_API_KEY=your_key_here
NOTION_API_KEY=your_key_here
NOTION_DB_ID=your_db_id_here
SLACK_WEBHOOK_URL=your_webhook_here
S3_BUCKET=your_bucket_here
```

4. Run locally:
```bash
./scripts/run_local.sh
```

### Docker Build

```bash
# Build image
docker build -t analyze-fx:latest .

# Run with docker-compose
docker-compose up
```

### ECS Deployment

1. Build and push to ECR:
```bash
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com
docker build -t analyze-fx .
docker tag analyze-fx:latest 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/analyze-fx:latest
docker push 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/analyze-fx:latest
```

2. Update ECS task definition with new image

3. Configure EventBridge Scheduler (see `config/scheduler/`)

## Project Structure

```
analyze_FX_chart/
├── src/
│   ├── analysis/         # Core analysis logic
│   ├── data_fetcher/     # TwelveData API client
│   ├── charting/         # Chart generation
│   ├── io/               # Notion, Slack, S3 clients
│   ├── runner/           # Main orchestrator
│   └── utils/            # Config, logging
├── config/               # Configuration files
├── memory/               # Analysis rules/memory
├── prompts/              # Analysis prompts
├── schema/               # JSON schemas
├── scripts/              # Utility scripts
└── tests/                # Test files
```

## Testing

Run smoke tests:
```bash
python scripts/smoke_test.py
```

## Configuration

See `CLAUDE.md` for detailed project instructions and configuration.

## License

Private repository - All rights reserved