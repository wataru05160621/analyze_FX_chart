#!/bin/bash
# Enhanced run_once script with retry and parameter override support

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
AWS_REGION="ap-northeast-1"
ACCOUNT_ID="455931011903"
CLUSTER_NAME="analyze-fx-cluster"
TASK_DEFINITION="analyze-fx"
S3_BUCKET="analyze-fx-455931011903-apne1"

# Parse arguments
MODE="${1:-dryrun}"
RETRY_LAST="${2:-false}"
CUSTOM_PAIR="${3:-}"
FORCE_TRADE="${4:-false}"

echo -e "${GREEN}=== FX Analysis Run (Enhanced) ===${NC}"
echo "Mode: $MODE"
echo "Retry Last: $RETRY_LAST"
echo "Custom Pair: ${CUSTOM_PAIR:-default}"
echo "Force Trade: $FORCE_TRADE"
echo ""

# Function to save run configuration
save_run_config() {
    local task_id=$1
    local config=$2
    
    echo "$config" | aws s3 cp - "s3://${S3_BUCKET}/configs/runs/${task_id}.json"
    echo "$config" | aws s3 cp - "s3://${S3_BUCKET}/configs/last_run.json"
}

# Function to load last run configuration
load_last_config() {
    aws s3 cp "s3://${S3_BUCKET}/configs/last_run.json" - 2>/dev/null || echo "{}"
}

# Build environment overrides
build_env_overrides() {
    local overrides='['
    
    # Base overrides
    overrides+="{\"name\": \"RUN_MODE\", \"value\": \"$MODE\"}"
    
    # Mode-specific overrides
    if [ "$MODE" = "dryrun" ]; then
        overrides+=",{\"name\": \"NOTION_TAG\", \"value\": \"TEST\"}"
        overrides+=",{\"name\": \"SLACK_CHANNEL_OVERRIDE\", \"value\": \"#fx-test\"}"
        overrides+=",{\"name\": \"S3_PREFIX_OVERRIDE\", \"value\": \"test/\"}"
        overrides+=",{\"name\": \"LOG_LEVEL\", \"value\": \"DEBUG\"}"
    else
        overrides+=",{\"name\": \"LOG_LEVEL\", \"value\": \"INFO\"}"
    fi
    
    # Custom pair override
    if [ -n "$CUSTOM_PAIR" ]; then
        overrides+=",{\"name\": \"PAIR_OVERRIDE\", \"value\": \"$CUSTOM_PAIR\"}"
    fi
    
    # Force trade override (skip quality gates for testing)
    if [ "$FORCE_TRADE" = "true" ]; then
        overrides+=",{\"name\": \"FORCE_TRADE\", \"value\": \"true\"}"
    fi
    
    # Retry metadata
    if [ "$RETRY_LAST" = "true" ]; then
        overrides+=",{\"name\": \"IS_RETRY\", \"value\": \"true\"}"
    fi
    
    overrides+=']'
    echo "$overrides"
}

# Main execution
main() {
    local env_overrides
    
    # Handle retry mode
    if [ "$RETRY_LAST" = "true" ]; then
        echo -e "${YELLOW}Loading last run configuration...${NC}"
        
        last_config=$(load_last_config)
        if [ "$last_config" = "{}" ]; then
            echo -e "${RED}No previous run configuration found${NC}"
            exit 1
        fi
        
        echo "Last run config loaded"
        # Extract relevant settings from last config
        # For now, just use the same mode
    fi
    
    # Build environment overrides
    env_overrides=$(build_env_overrides)
    
    # Confirm production run
    if [ "$MODE" = "production" ] && [ "$RETRY_LAST" != "true" ]; then
        echo -e "${YELLOW}⚠️  Production run will create real Notion pages and send Slack notifications${NC}"
        read -p "Continue? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Aborted"
            exit 0
        fi
    fi
    
    # Run ECS task
    echo -e "${YELLOW}Starting ECS task...${NC}"
    
    TASK_RESPONSE=$(aws ecs run-task \
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
                \"environment\": $env_overrides
            }]
        }" \
        --region "$AWS_REGION")
    
    TASK_ARN=$(echo "$TASK_RESPONSE" | jq -r '.tasks[0].taskArn')
    TASK_ID=$(echo "$TASK_ARN" | awk -F/ '{print $NF}')
    
    if [ -z "$TASK_ID" ]; then
        echo -e "${RED}Failed to start ECS task${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Task started: $TASK_ID${NC}"
    
    # Save run configuration
    RUN_CONFIG=$(jq -n \
        --arg mode "$MODE" \
        --arg task_id "$TASK_ID" \
        --arg pair "${CUSTOM_PAIR:-USDJPY}" \
        --arg force_trade "$FORCE_TRADE" \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{
            mode: $mode,
            task_id: $task_id,
            pair: $pair,
            force_trade: $force_trade,
            timestamp: $timestamp
        }')
    
    save_run_config "$TASK_ID" "$RUN_CONFIG"
    echo -e "${GREEN}✓ Configuration saved${NC}"
    
    # Monitor task
    echo -e "${YELLOW}Monitoring task execution...${NC}"
    
    LOG_GROUP="/ecs/analyze-fx"
    LOG_STREAM="ecs/analyze-fx/$TASK_ID"
    
    # Start log monitoring in background
    (
        sleep 10  # Wait for task to start
        aws logs tail "$LOG_GROUP" \
            --follow \
            --format short \
            --region "$AWS_REGION" \
            --filter-pattern "{ $.stream = \"$LOG_STREAM\" }" 2>/dev/null
    ) &
    
    LOG_PID=$!
    
    # Wait for task completion
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
    
    # Stop log monitoring
    kill $LOG_PID 2>/dev/null || true
    sleep 2
    
    # Get task result
    TASK_DETAILS=$(aws ecs describe-tasks \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ARN" \
        --region "$AWS_REGION" \
        --query 'tasks[0]')
    
    EXIT_CODE=$(echo "$TASK_DETAILS" | jq -r '.containers[0].exitCode')
    STOP_REASON=$(echo "$TASK_DETAILS" | jq -r '.stoppedReason // "N/A"')
    
    echo ""
    echo -e "${YELLOW}=== Task Complete ===${NC}"
    echo "Task ID: $TASK_ID"
    echo "Exit Code: $EXIT_CODE"
    echo "Stop Reason: $STOP_REASON"
    
    # Check success
    if [ "$EXIT_CODE" = "0" ]; then
        echo -e "${GREEN}✓ Analysis completed successfully${NC}"
        
        # Show recent outputs
        echo ""
        echo -e "${YELLOW}Recent S3 uploads:${NC}"
        aws s3 ls "s3://${S3_BUCKET}/charts/" \
            --recursive \
            --region "$AWS_REGION" \
            | tail -5
        
        echo ""
        echo -e "${GREEN}=== Success ===${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Check Slack for notification"
        echo "  2. Verify Notion page"
        echo "  3. Review S3 outputs"
        
        if [ "$MODE" = "dryrun" ]; then
            echo ""
            echo -e "${BLUE}Dry-run complete. Run production when ready:${NC}"
            echo "  $0 production"
        fi
        
    else
        echo -e "${RED}✗ Analysis failed${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check CloudWatch logs:"
        echo "     aws logs get-log-events --log-group-name $LOG_GROUP --log-stream-name $LOG_STREAM"
        echo "  2. Retry with same configuration:"
        echo "     $0 $MODE true"
        
        exit 1
    fi
}

# Run main function
main