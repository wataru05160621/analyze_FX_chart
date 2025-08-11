#!/bin/bash
# Run FX analysis once (dry-run or production)

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="ap-northeast-1"
ACCOUNT_ID="455931011903"
CLUSTER_NAME="analyze-fx-cluster"
TASK_DEFINITION="analyze-fx"

# Parse arguments
MODE="${1:-dryrun}"  # Default to dry-run
FOLLOW_LOGS="${2:-true}"  # Default to following logs

echo -e "${GREEN}=== FX Analysis One-Time Run ===${NC}"
echo "Mode: $MODE"
echo "Region: $AWS_REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# Set environment overrides based on mode
if [ "$MODE" = "dryrun" ]; then
    echo -e "${YELLOW}Running in DRY-RUN mode${NC}"
    echo "  • Notion: Test tag will be added"
    echo "  • Slack: Notifications enabled"
    echo "  • S3: Output enabled"
    echo ""
    
    ENV_OVERRIDES='[
        {"name": "RUN_MODE", "value": "dryrun"},
        {"name": "LOG_LEVEL", "value": "DEBUG"}
    ]'
elif [ "$MODE" = "production" ]; then
    echo -e "${YELLOW}Running in PRODUCTION mode${NC}"
    echo "  • Notion: Production page"
    echo "  • Slack: Notifications enabled"
    echo "  • S3: Output enabled"
    echo ""
    
    ENV_OVERRIDES='[
        {"name": "RUN_MODE", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"}
    ]'
else
    echo -e "${RED}Error: Invalid mode. Use 'dryrun' or 'production'${NC}"
    exit 1
fi

# Confirm production run
if [ "$MODE" = "production" ]; then
    echo -e "${YELLOW}⚠️  This will create a production Notion page and send Slack notifications.${NC}"
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# Run ECS task
echo -e "${YELLOW}Starting ECS task...${NC}"

TASK_ARN=$(aws ecs run-task \
    --cluster "$CLUSTER_NAME" \
    --task-definition "$TASK_DEFINITION" \
    --launch-type FARGATE \
    --network-configuration '{
        "awsvpcConfiguration": {
            "subnets": ["subnet-06fba36a849bb6647", "subnet-02aef8bf85b9ceb0d"],
            "securityGroups": ["sg-03cb601e40f6e32ac"],
            "assignPublicIp": "ENABLED"
        }
    }' \
    --overrides "{
        \"containerOverrides\": [{
            \"name\": \"analyze-fx\",
            \"environment\": $ENV_OVERRIDES
        }]
    }" \
    --region "$AWS_REGION" \
    --query 'tasks[0].taskArn' \
    --output text)

if [ -z "$TASK_ARN" ]; then
    echo -e "${RED}Error: Failed to start ECS task${NC}"
    exit 1
fi

TASK_ID=$(echo "$TASK_ARN" | awk -F/ '{print $NF}')
echo -e "${GREEN}✓ Task started: $TASK_ID${NC}"
echo ""

# Wait for task to start and get log stream
echo -e "${YELLOW}Waiting for task to start...${NC}"
sleep 10

# Get log stream name
LOG_GROUP="/ecs/analyze-fx"
LOG_STREAM="ecs/analyze-fx/$TASK_ID"

# Follow logs if requested
if [ "$FOLLOW_LOGS" = "true" ]; then
    echo -e "${YELLOW}Following task logs...${NC}"
    echo ""
    
    # Start tailing logs
    aws logs tail "$LOG_GROUP" \
        --follow \
        --format short \
        --region "$AWS_REGION" \
        --filter-pattern "{ $.stream = \"$LOG_STREAM\" }" &
    
    TAIL_PID=$!
    
    # Wait for task to complete
    while true; do
        TASK_STATUS=$(aws ecs describe-tasks \
            --cluster "$CLUSTER_NAME" \
            --tasks "$TASK_ARN" \
            --region "$AWS_REGION" \
            --query 'tasks[0].lastStatus' \
            --output text)
        
        if [ "$TASK_STATUS" = "STOPPED" ]; then
            break
        fi
        
        sleep 5
    done
    
    # Stop tailing logs
    kill $TAIL_PID 2>/dev/null || true
    sleep 2
else
    # Just wait for task completion
    echo "Waiting for task completion (not following logs)..."
    aws ecs wait tasks-stopped \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$AWS_REGION"
fi

# Get task exit code
EXIT_CODE=$(aws ecs describe-tasks \
    --cluster "$CLUSTER_NAME" \
    --tasks "$TASK_ARN" \
    --region "$AWS_REGION" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)

echo ""
echo -e "${YELLOW}=== Task Complete ===${NC}"
echo "Task ID: $TASK_ID"
echo "Exit Code: $EXIT_CODE"

# Check exit code
if [ "$EXIT_CODE" = "0" ]; then
    echo -e "${GREEN}✓ Analysis completed successfully${NC}"
    
    # Show recent S3 uploads
    echo ""
    echo -e "${YELLOW}Recent S3 uploads:${NC}"
    aws s3 ls s3://analyze-fx-455931011903-apne1/charts/ \
        --recursive \
        --region "$AWS_REGION" \
        | tail -5
    
    echo ""
    echo -e "${GREEN}=== Run Complete ===${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Check Slack for notification"
    echo "  2. Verify Notion page creation"
    echo "  3. Confirm S3 uploads (charts/ and results/)"
    
    if [ "$MODE" = "dryrun" ]; then
        echo ""
        echo -e "${BLUE}Dry-run successful! Run with 'production' mode when ready:${NC}"
        echo "  ./scripts/run_once.sh production"
    fi
else
    echo -e "${RED}✗ Analysis failed with exit code: $EXIT_CODE${NC}"
    echo ""
    echo "Check CloudWatch logs for details:"
    echo "  aws logs get-log-events --log-group-name $LOG_GROUP --log-stream-name $LOG_STREAM --region $AWS_REGION"
    exit 1
fi