#!/bin/bash
# Deploy EventBridge scheduler for FX analysis production
# Tokyo Pre-open & London Pre-open dual operation

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
echo -e "${GREEN}    Tokyo Pre-open & London Pre-open    ${NC}"
echo "Region: $AWS_REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Step 1: Disable old schedulers
echo -e "${YELLOW}Step 1: Disabling old schedulers...${NC}"

# Disable old 08:00 JST scheduler
OLD_SCHEDULER="analyze-fx-prod-0800-jst"
if aws scheduler get-schedule --name "$OLD_SCHEDULER" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Disabling old scheduler: $OLD_SCHEDULER"
    aws scheduler update-schedule \
        --name "$OLD_SCHEDULER" \
        --region "$AWS_REGION" \
        --state "DISABLED" >/dev/null 2>&1 || true
    echo -e "${GREEN}✓ Old scheduler disabled${NC}"
else
    echo "Old scheduler not found: $OLD_SCHEDULER"
fi

# Step 2: Create/Update Tokyo Pre-open scheduler (08:30 JST)
echo -e "${YELLOW}Step 2: Setting up Tokyo Pre-open scheduler (08:30 JST)...${NC}"

TOKYO_SCHEDULER="analyze-fx-tokyo-preopen"

# Check if targets file exists
if [ ! -f "targets/ecs_analyze_tokyo.json" ]; then
    echo -e "${RED}Error: targets/ecs_analyze_tokyo.json not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Try update first, then create if doesn't exist
if aws scheduler get-schedule --name "$TOKYO_SCHEDULER" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Updating existing Tokyo Pre-open scheduler..."
    aws scheduler update-schedule \
        --name "$TOKYO_SCHEDULER" \
        --region "$AWS_REGION" \
        --schedule-expression 'cron(30 8 ? * MON-FRI *)' \
        --schedule-expression-timezone 'Asia/Tokyo' \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file://targets/ecs_analyze_tokyo.json \
        --state "ENABLED" \
        --description "FX Analysis Tokyo Pre-open - Weekdays 08:30 JST"
else
    echo "Creating new Tokyo Pre-open scheduler..."
    aws scheduler create-schedule \
        --name "$TOKYO_SCHEDULER" \
        --region "$AWS_REGION" \
        --schedule-expression 'cron(30 8 ? * MON-FRI *)' \
        --schedule-expression-timezone 'Asia/Tokyo' \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file://targets/ecs_analyze_tokyo.json \
        --state "ENABLED" \
        --description "FX Analysis Tokyo Pre-open - Weekdays 08:30 JST"
fi

echo -e "${GREEN}✓ Tokyo Pre-open scheduler configured${NC}"

# Step 3: Create/Update London Pre-open scheduler (07:30 Europe/London)
echo -e "${YELLOW}Step 3: Setting up London Pre-open scheduler (07:30 Europe/London)...${NC}"

LONDON_SCHEDULER="analyze-fx-london-preopen"

# Check if targets file exists
if [ ! -f "targets/ecs_analyze_london.json" ]; then
    echo -e "${RED}Error: targets/ecs_analyze_london.json not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Try update first, then create if doesn't exist
if aws scheduler get-schedule --name "$LONDON_SCHEDULER" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Updating existing London Pre-open scheduler..."
    aws scheduler update-schedule \
        --name "$LONDON_SCHEDULER" \
        --region "$AWS_REGION" \
        --schedule-expression 'cron(30 7 ? * MON-FRI *)' \
        --schedule-expression-timezone 'Europe/London' \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file://targets/ecs_analyze_london.json \
        --state "ENABLED" \
        --description "FX Analysis London Pre-open - Weekdays 07:30 London time (DST aware)"
else
    echo "Creating new London Pre-open scheduler..."
    aws scheduler create-schedule \
        --name "$LONDON_SCHEDULER" \
        --region "$AWS_REGION" \
        --schedule-expression 'cron(30 7 ? * MON-FRI *)' \
        --schedule-expression-timezone 'Europe/London' \
        --flexible-time-window '{"Mode":"OFF"}' \
        --target file://targets/ecs_analyze_london.json \
        --state "ENABLED" \
        --description "FX Analysis London Pre-open - Weekdays 07:30 London time (DST aware)"
fi

echo -e "${GREEN}✓ London Pre-open scheduler configured${NC}"

# Step 4: Keep daily stats scheduler unchanged
echo -e "${YELLOW}Step 4: Verifying daily stats scheduler...${NC}"

STATS_SCHEDULER="analyze-fx-dailystats-2345-jst"
if aws scheduler get-schedule --name "$STATS_SCHEDULER" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Daily stats scheduler exists (23:45 JST)${NC}"
else
    echo -e "${YELLOW}Daily stats scheduler not found${NC}"
fi

# Step 5: List all schedulers
echo -e "${YELLOW}Step 5: Current schedulers:${NC}"
aws scheduler list-schedules \
    --region "$AWS_REGION" \
    --query 'Schedules[?contains(Name, `analyze-fx`)].{Name:Name,State:State,Expression:ScheduleExpression,Timezone:ScheduleExpressionTimezone}' \
    --output table

echo ""
echo -e "${GREEN}=== Scheduler Deployment Complete ===${NC}"
echo ""
echo "Active schedules:"
echo "  - Tokyo Pre-open:  Weekdays 08:30 JST"
echo "  - London Pre-open: Weekdays 07:30 London time (DST aware)"
echo "  - Daily Stats:     Daily 23:45 JST"
echo ""
echo "To manually test with SESSION:"
echo "  SESSION=tokyo_preopen ./scripts/run_once_v2.sh"
echo "  SESSION=london_preopen ./scripts/run_once_v2.sh"