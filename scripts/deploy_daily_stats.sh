#!/bin/bash
# Deploy daily stats job with EventBridge scheduler (23:45 JST)

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
TASK_FAMILY="analyze-fx-daily-stats"
SCHEDULER_ROLE_ARN="arn:aws:iam::455931011903:role/service-role/Amazon_EventBridge_Scheduler_ECS_a2bab3de69"
TASK_DEFINITION_FILE="config/ecs/task-definition-daily-stats.json"

echo -e "${GREEN}=== Daily Stats Job Deployment ===${NC}"
echo "Region: $AWS_REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Step 1: Create CloudWatch Log Group if not exists
echo -e "${YELLOW}Step 1: Creating CloudWatch Log Group...${NC}"
aws logs create-log-group \
    --log-group-name "/ecs/${TASK_FAMILY}" \
    --region "$AWS_REGION" 2>/dev/null || echo "Log group already exists"
echo -e "${GREEN}✓ Log group ready${NC}"

# Step 2: Register task definition
echo -e "${YELLOW}Step 2: Registering task definition...${NC}"

if [ -f "$TASK_DEFINITION_FILE" ]; then
    TASK_DEF_ARN=$(aws ecs register-task-definition \
        --cli-input-json file://"$TASK_DEFINITION_FILE" \
        --region "$AWS_REGION" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)
    echo -e "${GREEN}✓ Task definition registered: $TASK_DEF_ARN${NC}"
else
    echo -e "${RED}Error: Task definition file not found: $TASK_DEFINITION_FILE${NC}"
    exit 1
fi

# Step 3: Create/Update daily stats scheduler (23:45 JST)
echo -e "${YELLOW}Step 3: Creating daily stats scheduler (23:45 JST)...${NC}"

SCHEDULER_NAME="analyze-fx-dailystats-2345-jst"
SCHEDULE_EXPRESSION="cron(45 14 ? * * *)"  # 14:45 UTC = 23:45 JST

# Create scheduler target JSON
cat > /tmp/dailystats_target.json <<EOF
{
    "Arn": "arn:aws:ecs:${AWS_REGION}:${ACCOUNT_ID}:cluster/${CLUSTER_NAME}",
    "RoleArn": "${SCHEDULER_ROLE_ARN}",
    "EcsParameters": {
        "TaskDefinitionArn": "${TASK_DEF_ARN}",
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
if aws scheduler get-schedule --name "$SCHEDULER_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Updating existing daily stats scheduler..."
    aws scheduler update-schedule \
        --name "$SCHEDULER_NAME" \
        --region "$AWS_REGION" \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --schedule-expression-timezone "UTC" \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file:///tmp/dailystats_target.json \
        --state "ENABLED" \
        --description "FX Daily Stats Job - Every day 23:45 JST"
else
    echo "Creating new daily stats scheduler..."
    aws scheduler create-schedule \
        --name "$SCHEDULER_NAME" \
        --region "$AWS_REGION" \
        --schedule-expression "$SCHEDULE_EXPRESSION" \
        --schedule-expression-timezone "UTC" \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file:///tmp/dailystats_target.json \
        --state "ENABLED" \
        --description "FX Daily Stats Job - Every day 23:45 JST"
fi

echo -e "${GREEN}✓ Daily stats scheduler deployed: $SCHEDULER_NAME${NC}"

# Step 4: Verify deployment
echo -e "${YELLOW}Step 4: Verifying deployment...${NC}"

# Show task definition
echo "Task Definition:"
aws ecs describe-task-definition \
    --task-definition "$TASK_FAMILY" \
    --region "$AWS_REGION" \
    --query 'taskDefinition.{Family:family,Revision:revision,Status:status}' \
    --output table

# Show scheduler
echo ""
echo "Scheduler Status:"
aws scheduler get-schedule \
    --name "$SCHEDULER_NAME" \
    --region "$AWS_REGION" \
    --query '{Name:Name,State:State,Expression:ScheduleExpression,NextRun:NextExecutionTime}' \
    --output table

# Cleanup
rm -f /tmp/dailystats_target.json

echo -e "${GREEN}=== Daily Stats Job Deployment Complete ===${NC}"
echo ""
echo "Schedule: Every day 23:45 JST (14:45 UTC)"
echo "Task: $TASK_FAMILY"
echo "Next execution: $(aws scheduler get-schedule --name "$SCHEDULER_NAME" --region "$AWS_REGION" --query 'NextExecutionTime' --output text 2>/dev/null || echo 'N/A')"