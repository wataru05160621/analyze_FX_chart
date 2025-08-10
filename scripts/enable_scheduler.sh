#!/bin/bash
# Enable EventBridge Scheduler for FX Analysis

echo "🕐 Enabling FX Analysis Scheduler"
echo "=================================="

# Get current scheduler details
echo "📋 Current scheduler configuration:"
aws scheduler get-schedule \
  --name fx-analyzer-0800-jst \
  --region ap-northeast-1 \
  --query '{Name: Name, State: State, Schedule: ScheduleExpression}' \
  --output table

# Enable the scheduler
echo ""
echo "🔄 Enabling scheduler..."
aws scheduler update-schedule \
  --name fx-analyzer-0800-jst \
  --region ap-northeast-1 \
  --state ENABLED \
  --schedule-expression "cron(0 23 ? * MON-FRI *)" \
  --flexible-time-window '{"Mode": "OFF"}' \
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
      }
    },
    "RetryPolicy": {
      "MaximumRetryAttempts": 2,
      "MaximumEventAgeInSeconds": 3600
    }
  }' \
  --output json | jq '{Name: .Name, State: .State}'

echo ""
echo "✅ Scheduler has been enabled!"
echo ""
echo "📅 Schedule Details:"
echo "  - Time: Every weekday at 8:00 AM JST"
echo "  - Days: Monday to Friday"
echo "  - Timezone: Asia/Tokyo (UTC+9)"
echo ""
echo "Next executions (JST):"
echo "  - Tomorrow 8:00 AM (if weekday)"
echo "  - Or next Monday 8:00 AM"
echo ""
echo "To disable scheduler, run:"
echo "  aws scheduler update-schedule --name fx-analyzer-0800-jst --state DISABLED --region ap-northeast-1"