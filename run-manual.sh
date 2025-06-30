#!/bin/bash
# FXチャート分析の手動実行スクリプト

echo "🚀 FXチャート分析を手動実行します..."
echo "実行時刻: $(date '+%Y年%m月%d日 %H時%M分')"

# ECSタスクを実行
TASK_ARN=$(aws ecs run-task \
  --cluster fx-analyzer-cluster-prod \
  --task-definition fx-analyzer-prod:15 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0065f9abccaa2378e,subnet-074d09d0382db1cc3],securityGroups=[sg-00deccd6d44a238ee],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"fx-analyzer","environment":[{"name":"EXECUTION_SOURCE","value":"manual"}]}]}' \
  --query 'tasks[0].taskArn' \
  --output text)

if [ $? -eq 0 ]; then
    echo "✅ タスクが開始されました"
    echo "タスクARN: $TASK_ARN"
    echo ""
    echo "📊 実行状況の確認:"
    echo "1. CloudWatch Logsでログを確認:"
    echo "   https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1#logsV2:log-groups/log-group/\$252Fecs\$252Ffx-analyzer-prod"
    echo ""
    echo "2. タスクの状態を確認:"
    echo "   aws ecs describe-tasks --cluster fx-analyzer-cluster-prod --tasks $TASK_ARN --query 'tasks[0].lastStatus'"
    echo ""
    echo "3. 実行完了まで約2-3分かかります"
else
    echo "❌ タスクの開始に失敗しました"
    exit 1
fi