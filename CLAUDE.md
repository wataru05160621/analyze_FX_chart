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
1. Plan modules (`analysis/core`, `io/notion`, `io/slack`, `io/s3`, `runner`).
2. Implement analysis to emit narrative + JSON (schema).
3. Implement Notion upsert, Slack post, S3 save.
4. Add retries, smoke scripts, unit tests.

## Runtime
Cluster: analyze-fx-cluster
TaskDef: analyze-fx (256/512)
Network: subnets ['subnet-06fba36a849bb6647', 'subnet-02aef8bf85b9ceb0d'], SG sg-03cb601e40f6e32ac, AssignPublicIp=ENABLED
Scheduler RoleArn: arn:aws:iam::455931011903:role/service-role/Amazon_EventBridge_Scheduler_ECS_a2bab3de69

## Env
Non-secrets: APP_NAME,TZ,PAIR,TIMEFRAMES,S3_PREFIX,LOG_LEVEL
Secrets: NOTION_API_KEY, NOTION_DB_ID, SLACK_WEBHOOK_URL, S3_BUCKET
