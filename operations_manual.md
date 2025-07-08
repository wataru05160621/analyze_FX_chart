# FXチャート分析システム 運用手順書

## システム概要

### アーキテクチャ
```
EventBridge (定時実行) → ECS Fargate → Chart Generation → Claude Analysis → Notion
                                    ↓
                              S3 (chart storage)
                                    ↓
                            CloudWatch (monitoring)
```

### 実行スケジュール
- **朝**: JST 8:00 AM (UTC 23:00 前日)
- **午後**: JST 3:00 PM (UTC 6:00)
- **夜**: JST 9:00 PM (UTC 12:00)

## 日常運用

### 1. **毎日の確認事項**

#### 実行状況の確認
```bash
# 過去24時間のタスク実行履歴
aws ecs list-tasks \
    --cluster fx-analyzer-cluster-prod \
    --started-by "aws-events"

# 成功/失敗のステータス確認
aws logs filter-log-events \
    --log-group-name /ecs/fx-analyzer-prod \
    --start-time $(date -d "1 day ago" +%s)000 \
    --filter-pattern "SUCCESS|ERROR"
```

#### Notion書き込み確認
- **確認項目**: 3回/日の分析結果が正常に記録されているか
- **アクセス**: [Notionデータベース](https://notion.so/your-database)
- **確認内容**:
  - 最新エントリの日時
  - チャート画像の添付
  - 分析内容の品質

#### CloudWatchメトリクス確認
```bash
# タスク失敗件数の確認
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name TaskStoppedReason \
    --start-time $(date -d "1 day ago" -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Sum
```

### 2. **週次の確認事項**

#### ログローテーションの確認
```bash
# ログサイズと使用量の確認
aws logs describe-log-groups \
    --log-group-name-prefix /ecs/fx-analyzer

# 古いログの削除状況確認（14日保持設定）
aws logs describe-log-streams \
    --log-group-name /ecs/fx-analyzer-prod \
    --order-by LastEventTime \
    --descending
```

#### S3ストレージ使用量確認
```bash
# チャート画像の容量確認
aws s3 ls s3://fx-analyzer-charts-ecs-prod-455931011903 \
    --summarize --human-readable --recursive

# 30日経過画像の自動削除確認
aws s3api get-bucket-lifecycle-configuration \
    --bucket fx-analyzer-charts-ecs-prod-455931011903
```

#### コスト使用状況確認
```bash
# 過去7日間のECS使用料金
aws ce get-cost-and-usage \
    --time-period Start=$(date -d "7 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity DAILY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

### 3. **月次の確認事項**

#### セキュリティ更新
```bash
# Docker基盤イメージの更新確認
docker pull python:3.11-slim

# 依存パッケージのセキュリティ更新
pip list --outdated
pip-audit  # セキュリティ脆弱性チェック
```

#### APIキーの確認
```bash
# Secrets Managerの値を確認
aws secretsmanager get-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --query SecretString --output text
```

## トラブルシューティング

### 1. **タスク実行失敗**

#### 症状: ECSタスクが起動しない
```bash
# タスク詳細確認
TASK_ARN=$(aws ecs list-tasks --cluster fx-analyzer-cluster-prod --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster fx-analyzer-cluster-prod --tasks $TASK_ARN

# 対処法:
# 1. タスク定義のリソース不足確認
# 2. セキュリティグループの設定確認
# 3. サブネットの設定確認
```

#### 症状: タスクは起動するが分析が失敗する
```bash
# ログで詳細エラーを確認
aws logs get-log-events \
    --log-group-name /ecs/fx-analyzer-prod \
    --log-stream-name $(aws logs describe-log-streams \
        --log-group-name /ecs/fx-analyzer-prod \
        --order-by LastEventTime --descending \
        --max-items 1 --query 'logStreams[0].logStreamName' --output text)

# 対処法:
# 1. APIキーの有効性確認
# 2. Notion接続確認
# 3. 外部API(yfinance)の状態確認
```

### 2. **パフォーマンス問題**

#### 症状: 実行時間が異常に長い
```bash
# CloudWatchメトリクスで実行時間確認
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name TaskRunTime \
    --start-time $(date -d "7 days ago" -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Average,Maximum

# 対処法:
# 1. CPU/メモリリソースの増加検討
# 2. チャート生成の最適化
# 3. 外部API応答時間の確認
```

### 3. **通知問題**

#### 症状: SNSアラートが届かない
```bash
# SNSトピックの状態確認
aws sns get-topic-attributes \
    --topic-arn $(aws cloudformation describe-stacks \
        --stack-name fx-analyzer-ecs-prod \
        --query 'Stacks[0].Outputs[?OutputKey==`AlertTopicArn`].OutputValue' \
        --output text)

# サブスクリプション確認
aws sns list-subscriptions-by-topic \
    --topic-arn $TOPIC_ARN

# 対処法:
# 1. メールアドレスの確認
# 2. サブスクリプションの再作成
# 3. 迷惑メールフォルダの確認
```

## 運用操作

### 1. **手動実行**

#### 緊急時の手動分析実行
```bash
# 手動タスク実行
aws ecs run-task \
    --cluster fx-analyzer-cluster-prod \
    --task-definition fx-analyzer-prod:LATEST \
    --launch-type FARGATE \
    --network-configuration 'awsvpcConfiguration={
        subnets=[subnet-xxx],
        securityGroups=[sg-xxx],
        assignPublicIp=ENABLED
    }'
```

#### スケジュール一時停止
```bash
# EventBridgeルールを無効化
aws events disable-rule --name fx-analyzer-morning-prod
aws events disable-rule --name fx-analyzer-afternoon-prod
aws events disable-rule --name fx-analyzer-evening-prod

# 再有効化
aws events enable-rule --name fx-analyzer-morning-prod
aws events enable-rule --name fx-analyzer-afternoon-prod
aws events enable-rule --name fx-analyzer-evening-prod
```

### 2. **設定変更**

#### APIキーの更新
```bash
# Secrets Managerの値を更新
aws secretsmanager put-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --secret-string '{
        "OPENAI_API_KEY": "new-key",
        "CLAUDE_API_KEY": "new-key",
        "NOTION_API_KEY": "new-key",
        "NOTION_DATABASE_ID": "new-id",
        "ANALYSIS_MODE": "claude",
        "USE_WEB_CHATGPT": "false"
    }'
```

#### スケジュール変更
```bash
# template-ecs.yamlを編集してre-deploy
# 例: 朝の実行時間を9:00 AMに変更
ScheduleExpression: "cron(0 0 * * ? *)"  # UTC 0:00 = JST 9:00 AM

# 再デプロイ
./deploy-ecs.sh
```

### 3. **メンテナンス操作**

#### システム更新
```bash
# 1. 新しいDockerイメージをビルド
docker build -t fx-analyzer .

# 2. ECRにプッシュ
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name fx-analyzer-ecs-prod \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
    --output text)
docker tag fx-analyzer:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

# 3. ECSサービスを強制更新
aws ecs update-service \
    --cluster fx-analyzer-cluster-prod \
    --service fx-analyzer-service \
    --force-new-deployment
```

#### データベースクリーンアップ
```python
# 古いNotionページの削除スクリプト（月次実行）
import os
from notion_client import Client
from datetime import datetime, timedelta

def cleanup_old_notion_pages():
    notion = Client(auth=os.environ["NOTION_API_KEY"])
    database_id = os.environ["NOTION_DATABASE_ID"]

    # 90日以前のページを削除
    cutoff_date = datetime.now() - timedelta(days=90)

    pages = notion.databases.query(
        database_id=database_id,
        filter={
            "property": "Created",
            "date": {
                "before": cutoff_date.isoformat()
            }
        }
    )

    for page in pages["results"]:
        notion.pages.update(
            page_id=page["id"],
            archived=True
        )
```

## パフォーマンス最適化

### 1. **リソース調整**
```yaml
# template-ecs.yamlでCPU/メモリを調整
TaskDefinition:
  Cpu: 2048     # 2 vCPU (現在: 1024)
  Memory: 4096  # 4GB (現在: 2048)
```

### 2. **チャート生成最適化**
```python
# chart_generator.pyで最適化可能な項目
- 画像解像度の調整 (dpi設定)
- 描画するろうそく足数の最適化
- キャッシュ機能の追加
```

### 3. **ネットワーク最適化**
```yaml
# プライベートサブネット + NATゲートウェイの使用
# (現在はパブリックサブネット使用)
```

## セキュリティ対策

### 1. **定期確認項目**
- [ ] APIキーの定期ローテーション（3ヶ月）
- [ ] Docker基盤イメージの更新（月次）
- [ ] 依存パッケージの脆弱性確認（週次）
- [ ] CloudTrailログの確認（月次）

### 2. **セキュリティ監査**
```bash
# VPCセキュリティグループの確認
aws ec2 describe-security-groups \
    --group-ids $(aws cloudformation describe-stack-resources \
        --stack-name fx-analyzer-ecs-prod \
        --logical-resource-id ECSSecurityGroup \
        --query 'StackResources[0].PhysicalResourceId' --output text)

# IAMロールの権限確認
aws iam get-role-policy \
    --role-name $(aws cloudformation describe-stack-resources \
        --stack-name fx-analyzer-ecs-prod \
        --logical-resource-id ECSTaskRole \
        --query 'StackResources[0].PhysicalResourceId' --output text) \
    --policy-name FXAnalyzerTaskPolicy
```

## 緊急時対応

### 1. **システム停止手順**
```bash
# 1. スケジュール実行を停止
aws events disable-rule --name fx-analyzer-morning-prod
aws events disable-rule --name fx-analyzer-afternoon-prod
aws events disable-rule --name fx-analyzer-evening-prod

# 2. 実行中タスクを停止
aws ecs stop-task \
    --cluster fx-analyzer-cluster-prod \
    --task $(aws ecs list-tasks --cluster fx-analyzer-cluster-prod --query 'taskArns[0]' --output text)
```

### 2. **データ復旧手順**
```bash
# バックアップから設定復元
aws secretsmanager put-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --secret-string file://backup-secrets.json

# システム再起動
./deploy-ecs.sh
```

## 連絡先・エスカレーション

### 技術担当
- **主担当**: システム管理者
- **副担当**: 開発チーム

### 緊急時連絡先
- **Level 1**: メール通知 (SNS)
- **Level 2**: Slack アラート
- **Level 3**: 電話連絡

## SLA (Service Level Agreement)

### 可用性目標
- **稼働率**: 99.5% (月間3.6時間のダウンタイム許容)
- **実行成功率**: 95% (週21回中20回成功)

### パフォーマンス目標
- **実行時間**: 10分以内/回
- **復旧時間**: 2時間以内

この運用手順書に従って、システムの安定稼働と継続的改善を実現してください。
