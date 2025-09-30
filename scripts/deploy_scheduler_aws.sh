#!/bin/bash
# Deploy scheduler configuration to AWS EventBridge

set -e

echo "🚀 Deploying FX Analyzer Scheduler to AWS..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please configure AWS CLI."
    exit 1
fi

# Set variables
REGION="ap-northeast-1"
SCHEDULE_CONFIG="config/scheduler/tokyo_london_30min.schedule.json"

echo "📍 Region: $REGION"
echo "📄 Config file: $SCHEDULE_CONFIG"

# Function to create or update scheduler
create_or_update_scheduler() {
    local name=$1
    local expression=$2
    local description=$3
    local session=$4
    
    echo ""
    echo "⏰ Configuring scheduler: $name"
    echo "   Schedule: $expression"
    echo "   Session: $session"
    
    # Check if scheduler exists
    if aws scheduler get-schedule --name "$name" --region "$REGION" &> /dev/null; then
        echo "   Updating existing scheduler..."
        
        # Update existing scheduler
        aws scheduler update-schedule \
            --name "$name" \
            --region "$REGION" \
            --schedule-expression "$expression" \
            --schedule-expression-timezone "Asia/Tokyo" \
            --flexible-time-window Mode=OFF \
            --target '{
                "Arn": "arn:aws:ecs:ap-northeast-1:455931011903:cluster/analyze-fx-cluster",
                "RoleArn": "arn:aws:iam::455931011903:role/service-role/Amazon_EventBridge_Scheduler_ECS_a2bab3de69",
                "EcsParameters": {
                    "TaskDefinitionArn": "arn:aws:ecs:ap-northeast-1:455931011903:task-definition/analyze-fx",
                    "LaunchType": "FARGATE",
                    "NetworkConfiguration": {
                        "awsvpcConfiguration": {
                            "Subnets": ["subnet-06fba36a849bb6647", "subnet-02aef8bf85b9ceb0d"],
                            "SecurityGroups": ["sg-03cb601e40f6e32ac"],
                            "AssignPublicIp": "ENABLED"
                        }
                    },
                    "TaskCount": 1,
                    "PlatformVersion": "LATEST"
                }
            }' \
            --description "$description" \
            --state "ENABLED"
    else
        echo "   Creating new scheduler..."
        
        # Create new scheduler
        aws scheduler create-schedule \
            --name "$name" \
            --region "$REGION" \
            --schedule-expression "$expression" \
            --schedule-expression-timezone "Asia/Tokyo" \
            --flexible-time-window Mode=OFF \
            --target '{
                "Arn": "arn:aws:ecs:ap-northeast-1:455931011903:cluster/analyze-fx-cluster",
                "RoleArn": "arn:aws:iam::455931011903:role/service-role/Amazon_EventBridge_Scheduler_ECS_a2bab3de69",
                "EcsParameters": {
                    "TaskDefinitionArn": "arn:aws:ecs:ap-northeast-1:455931011903:task-definition/analyze-fx",
                    "LaunchType": "FARGATE",
                    "NetworkConfiguration": {
                        "awsvpcConfiguration": {
                            "Subnets": ["subnet-06fba36a849bb6647", "subnet-02aef8bf85b9ceb0d"],
                            "SecurityGroups": ["sg-03cb601e40f6e32ac"],
                            "AssignPublicIp": "ENABLED"
                        }
                    },
                    "TaskCount": 1,
                    "PlatformVersion": "LATEST"
                }
            }' \
            --description "$description" \
            --state "ENABLED"
    fi
    
    if [ $? -eq 0 ]; then
        echo "   ✅ $name configured successfully"
    else
        echo "   ❌ Failed to configure $name"
        return 1
    fi
}

# Deploy Tokyo session scheduler (9:30 JST)
create_or_update_scheduler \
    "fx-analyzer-tokyo-30min" \
    "cron(30 9 ? * MON-FRI *)" \
    "FX Analysis 30 minutes after Tokyo market open (9:30 JST)" \
    "Tokyo"

# Deploy London session scheduler (16:00 JST)
create_or_update_scheduler \
    "fx-analyzer-london-30min" \
    "cron(0 16 ? * MON-FRI *)" \
    "FX Analysis 30 minutes after London market open (16:00 JST)" \
    "London"

echo ""
echo "📋 Verifying deployments..."

# List all FX analyzers
echo ""
echo "Active FX Analyzer Schedules:"
aws scheduler list-schedules \
    --region "$REGION" \
    --name-prefix "fx-analyzer" \
    --query 'Schedules[].{Name:Name,Expression:ScheduleExpression,State:State}' \
    --output table

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📌 Next steps:"
echo "   1. Monitor CloudWatch logs for execution results"
echo "   2. Check Notion database for analysis entries"
echo "   3. Verify Slack notifications are working"
echo ""
echo "🔍 To view logs:"
echo "   aws logs tail /ecs/analyze-fx --follow --region $REGION"