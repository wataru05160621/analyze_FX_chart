# CLAUDE.md — analyze_FX_chart (Fargate MVP)

## Goal
Automated FX analyzer to Notion + Slack + S3 via Fargate. Follow `/memory/SERENA_MCP_MEMORY.md` and `/prompts/ANALYSIS_PROMPT_TEMPLATE.md`.

## Repo pointers
- memory/SERENA_MCP_MEMORY.md
- prompts/ANALYSIS_PROMPT_TEMPLATE.md
- schema/analysis_output.schema.json
- config/terraform/dev.tfvars, prod.tfvars
- config/scheduler/dev.schedule.full.json, prod.schedule.full.json
- config/secrets/secrets_template.json
- arch/ARCH_FARGATE_MVP.md

## Tasks
1. Plan modules (`analysis/core`, `io/notion`, `io/slack`, `io/s3`, `data_fetcher/twelvedata`, `charting/mpl`, `runner`).
2. Implement analysis to emit narrative + JSON (schema) — must include both 5m & 1h.
3. Implement data fetch via **TwelveData** (no yfinance). Secrets: `TWELVEDATA_API_KEY`; Env: `DATA_SOURCE=twelvedata`, `SYMBOL=USD/JPY`.
4. Render charts (matplotlib) for 5m & 1h, store to S3 as `charts/{pair}/{yyyy-mm-dd}/{run_id}_{tf}.png` and pre-sign.
5. Create Notion page with properties + **image blocks** attaching the pre-signed URLs; optionally fill DB `Charts` (files) property.
6. Post Slack summary; include chart URLs if needed.
7. Add retries, smoke scripts, and unit tests.

## Runtime
Cluster: analyze-fx-cluster
TaskDef: analyze-fx (256/512)
Network: subnets ['subnet-06fba36a849bb6647', 'subnet-02aef8bf85b9ceb0d'], SG sg-03cb601e40f6e32ac, AssignPublicIp=ENABLED
Scheduler RoleArn: arn:aws:iam::455931011903:role/service-role/Amazon_EventBridge_Scheduler_ECS_a2bab3de69

## Env
Non-secrets: APP_NAME,TZ,PAIR,TIMEFRAMES,S3_PREFIX,LOG_LEVEL,DATA_SOURCE,SYMBOL
Secrets: NOTION_API_KEY, NOTION_DB_ID, SLACK_WEBHOOK_URL, S3_BUCKET, TWELVEDATA_API_KEY

## Data Source
- Use **TwelveData** time_series API. Implement `data_fetcher/twelvedata.py` with helpers:
  - `fetch_timeseries(symbol, interval)` returning clean DataFrame (UTC→JST aware).
  - Handle rate limits and retries.
- Intervals required: **5min** and **1h**.

## Charts & Notion
- Render PNG charts for **5m** and **1h** (matplotlib). Save to S3 as `charts/{pair}/{yyyy-mm-dd}/{run_id}_5m.png` and `_1h.png`.
- Generate **pre‑signed URLs（>= 5分）** and attach to Notion page:
  - Page blocks: `image` with `external.url` set to the pre‑signed URL。
  - DB property `Charts` (type **files**) に外部URLとしても格納可。
- JSON must include `charts` array for both timeframes + URLs.

## Definition of Done
- One run writes Notion page (text + 2 images), Slack message, S3 artifacts (2 PNG + JSON).
- Output JSON validates against `/schema/analysis_output.schema.json`.
- Narrative avoids investment advice; uses EV language.
- Idempotent by `RunId`.
