#!/bin/bash
# 今朝の実行ログを確認するスクリプト

echo "=== 今朝（8:00）の実行ログを確認 ==="
echo

# 日本時間8:00はUTC23:00（前日）
# 今日の日付を取得
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)

echo "検索期間:"
echo "  開始: ${YESTERDAY} 22:50 UTC (日本時間 ${TODAY} 07:50)"
echo "  終了: ${YESTERDAY} 23:10 UTC (日本時間 ${TODAY} 08:10)"
echo

# CloudWatch Logsから今朝の実行ログを取得
echo "=== ECS実行ログ ==="
aws logs filter-log-events \
    --log-group-name /ecs/fx-analyzer-prod \
    --start-time $(date -v-1d -v22H -v50M -v0S +%s000 2>/dev/null || date -d "${YESTERDAY} 22:50:00" +%s000) \
    --end-time $(date -v-1d -v23H -v10M -v0S +%s000 2>/dev/null || date -d "${YESTERDAY} 23:10:00" +%s000) \
    --query 'events[*].[timestamp,message]' \
    --output text | while IFS=$'\t' read -r timestamp message; do
    # タイムスタンプを日本時間に変換
    jst_time=$(date -r $((timestamp/1000)) +"%Y-%m-%d %H:%M:%S JST" 2>/dev/null || date -d "@$((timestamp/1000))" +"%Y-%m-%d %H:%M:%S JST")
    echo "[$jst_time] $message"
done

echo
echo "=== 実行結果の確認 ==="

# 最新のタスク実行を確認
echo "最新のECSタスク実行状況:"
aws ecs list-tasks \
    --cluster fx-analyzer-cluster-prod \
    --desired-status STOPPED \
    --query 'taskArns[0:5]' \
    --output json | jq -r '.[]' | while read task_arn; do
    
    task_details=$(aws ecs describe-tasks \
        --cluster fx-analyzer-cluster-prod \
        --tasks "$task_arn" \
        --query 'tasks[0].[createdAt,stoppedAt,stopCode,stoppedReason]' \
        --output json)
    
    created_at=$(echo $task_details | jq -r '.[0]')
    stopped_at=$(echo $task_details | jq -r '.[1]')
    stop_code=$(echo $task_details | jq -r '.[2]')
    stopped_reason=$(echo $task_details | jq -r '.[3]')
    
    # 今朝の実行かチェック（UTC 22:50-23:10）
    created_hour=$(date -d "$created_at" +%H 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$created_at" +%H 2>/dev/null)
    created_date=$(date -d "$created_at" +%Y-%m-%d 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$created_at" +%Y-%m-%d 2>/dev/null)
    
    if [[ "$created_date" == "$YESTERDAY" ]] && [[ "$created_hour" == "23" ]]; then
        echo
        echo "タスク: $(basename $task_arn)"
        echo "  開始時刻: $created_at (UTC)"
        echo "  終了時刻: $stopped_at (UTC)"
        echo "  終了コード: $stop_code"
        echo "  終了理由: $stopped_reason"
    fi
done

echo
echo "=== Notion確認 ==="
echo "Notionで今朝の投稿を確認してください:"
echo "https://notion.so/your-database-id"

echo
echo "=== WordPress確認 ==="
echo "WordPressで今朝の投稿を確認してください:"
echo "https://by-price-action.com/"

echo
echo "=== 詳細ログの取得方法 ==="
echo "より詳細なログを見るには:"
echo "  aws logs tail /ecs/fx-analyzer-prod --follow --since 1h"
echo
echo "特定のエラーを検索:"
echo "  aws logs tail /ecs/fx-analyzer-prod --filter-pattern \"ERROR\" --since 1h"