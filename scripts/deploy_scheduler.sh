#!/bin/bash
# Deploy EventBridge scheduler for FX analysis production

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="ap-northeast-1"
ACCOUNT_ID="455931011903"
CLUSTER_NAME="analyze-fx-cluster"
TASK_DEFINITION="analyze-fx"
SCHEDULER_ROLE_ARN="arn:aws:iam::455931011903:role/service-role/Amazon_EventBridge_Scheduler_ECS_a2bab3de69"

echo -e "${GREEN}=== EventBridge Scheduler Deployment ===${NC}"
echo "Region: $AWS_REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Step 1: Disable/Delete existing 30-minute scheduler if exists
echo -e "${YELLOW}Step 1: Cleaning up old schedulers...${NC}"

OLD_SCHEDULER="fx-analysis-v2-every-30min"
if aws scheduler get-schedule --name "$OLD_SCHEDULER" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Disabling old scheduler: $OLD_SCHEDULER"
    aws scheduler update-schedule \
        --name "$OLD_SCHEDULER" \
        --region "$AWS_REGION" \
        --state "DISABLED" \
        --schedule-expression "rate(30 minutes)" \
        --flexible-time-window '{"mode":"OFF"}' \
        --target '{"arn":"arn:aws:ecs:'$AWS_REGION':'$ACCOUNT_ID':cluster/'$CLUSTER_NAME'","roleArn":"'$SCHEDULER_ROLE_ARN'"}' 2>/dev/null || true
    
    echo "Deleting old scheduler: $OLD_SCHEDULER"
    aws scheduler delete-schedule --name "$OLD_SCHEDULER" --region "$AWS_REGION" 2>/dev/null || true
    echo -e "${GREEN}✓ Old scheduler cleaned up${NC}"
fi

# Step 2: Create/Update production scheduler (08:00 JST weekdays)
echo -e "${YELLOW}Step 2: Creating production scheduler (08:00 JST weekdays)...${NC}"

PROD_SCHEDULER="analyze-fx-prod-0800-jst"
SCHEDULE_EXPRESSION="cron(0 23 ? * SUN-THU *)"  # 23:00 UTC(Sun-Thu) = 08:00 JST(Mon-Fri)

# Create scheduler JSON payload
cat > /tmp/scheduler_target.json <<EOF
{
    "Arn": "arn:aws:ecs:${AWS_REGION}:${ACCOUNT_ID}:cluster/${CLUSTER_NAME}",
    "RoleArn": "${SCHEDULER_ROLE_ARN}",
    "EcsParameters": {
        "TaskDefinitionArn": "arn:aws:ecs:${AWS_REGION}:${ACCOUNT_ID}:task-definition/${TASK_DEFINITION}",
        "LaunchType": "FARGATE",
        "NetworkConfiguration": {
            "awsvpcConfiguration": {
                "AssignPublicIp": "ENABLED",
                "Subnets": [
                    "subnet-06fba36a849bb6647",
                    "subnet-02aef8bf85b9ceb0d"
                ],
                "SecurityGroups": ["sg-03cb601e40f6e32ac"]
            }
        },
        "TaskCount": 1,
        "PlatformVersion": "LATEST"
    }
}
EOF

# Check if scheduler exists
if aws scheduler get-schedule --name "$PROD_SCHEDULER" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Updating existing production scheduler..."
    aws scheduler update-schedule \
        --name "$PROD_SCHEDULER" \
        --region "$AWS_REGION" \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --schedule-expression-timezone "UTC" \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file:///tmp/scheduler_target.json \
        --state "ENABLED" \
        --description "FX Analysis Production - Weekdays 08:00 JST"
else
    echo "Creating new production scheduler..."
    aws scheduler create-schedule \
        --name "$PROD_SCHEDULER" \
        --region "$AWS_REGION" \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --schedule-expression-timezone "UTC" \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file:///tmp/scheduler_target.json \
        --state "ENABLED" \
        --description "FX Analysis Production - Weekdays 08:00 JST"
fi

echo -e "${GREEN}✓ Production scheduler deployed: $PROD_SCHEDULER${NC}"

# Step 3: List current schedulers
echo -e "${YELLOW}Step 3: Current schedulers:${NC}"
aws scheduler list-schedules \
    --region "$AWS_REGION" \
    --query 'Schedules[?contains(Name, `fx`)].{Name:Name,State:State,Expression:ScheduleExpression}' \
    --output table

# Cleanup
rm -f /tmp/scheduler_target.json

echo -e "${GREEN}=== Scheduler Deployment Complete ===${NC}"
echo ""
echo "Production schedule: Weekdays 08:00 JST (23:00 UTC)"
echo "Next execution: $(aws scheduler get-schedule --name "$PROD_SCHEDULER" --region "$AWS_REGION" --query 'NextExecutionTime' --output text 2>/dev/null || echo 'N/A')"