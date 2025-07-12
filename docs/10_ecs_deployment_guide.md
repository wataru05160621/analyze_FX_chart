# ECS Fargate デプロイガイド

## 概要

ECS Fargateを使用することで、高品質なチャート生成（yfinance + mplfinance + matplotlib）を維持しながら、AWS上で定時実行システムを構築できます。

## アーキテクチャ

```
EventBridge (cron) → ECS Fargate Task → Chart Generation → Claude Analysis → Notion
                                     ↓
                               S3 (chart storage)
                                     ↓
                             CloudWatch (monitoring)
```

## 必要な準備

### 1. Dockerのインストール確認
```bash
docker --version
# Docker version 20.10.x 以上
```

### 2. 環境変数設定
```bash
# .envファイルに以下を設定
export OPENAI_API_KEY="sk-proj-your-key"
export CLAUDE_API_KEY="sk-ant-your-key"  
export NOTION_API_KEY="ntn_your-key"
export NOTION_DATABASE_ID="your-database-id"
export ALERT_EMAIL="wataru.s.05160621@gmail.com"
```

## デプロイ手順

### 1. 自動デプロイ（推奨）
```bash
# すべて自動で実行
./deploy-ecs.sh
```

### 2. 手動デプロイ
```bash
# 1. CloudFormationスタックをデプロイ
aws cloudformation deploy \
    --template-file template-ecs.yaml \
    --stack-name fx-analyzer-ecs-prod \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        Environment=prod \
        AlertEmail=wataru.s.05160621@gmail.com

# 2. ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | \
    docker login --username AWS --password-stdin 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com

# 3. Dockerイメージをビルド・プッシュ
docker build -t fx-analyzer .
docker tag fx-analyzer:latest 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/fx-analyzer-prod:latest
docker push 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/fx-analyzer-prod:latest

# 4. Secrets Managerを設定
aws secretsmanager put-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --secret-string '{
        "OPENAI_API_KEY": "your-key",
        "CLAUDE_API_KEY": "your-key",
        "NOTION_API_KEY": "your-key", 
        "NOTION_DATABASE_ID": "your-id",
        "ANALYSIS_MODE": "claude",
        "USE_WEB_CHATGPT": "false"
    }'
```

## 設定されるリソース

### 1. ネットワーク
- **VPC**: 10.0.0.0/16
- **パブリックサブネット**: 2つのAZ
- **インターネットゲートウェイ**: 外部通信用
- **セキュリティグループ**: HTTPS Outbound

### 2. ECS
- **クラスター**: Fargateクラスター
- **タスク定義**: 1 vCPU, 2GB RAM
- **コンテナ**: Python 3.11 + 全依存関係

### 3. スケジュール
- **朝**: JST 8:00 AM (UTC 23:00 前日)
- **午後**: JST 3:00 PM (UTC 6:00)
- **夜**: JST 9:00 PM (UTC 12:00)

### 4. 監視
- **CloudWatch Logs**: タスク実行ログ
- **CloudWatch Alarms**: タスク失敗監視
- **SNS**: メール通知

## コスト見積もり

### ECS Fargate使用料金
```
タスク実行時間: 約10分/回
CPU: 1 vCPU × 0.167時間 × 90回/月 = 15 vCPU-時間/月
メモリ: 2GB × 0.167時間 × 90回/月 = 30 GB-時間/月

vCPU料金: 15 × $0.04048 = $0.61/月
メモリ料金: 30 × $0.004445 = $0.13/月
合計: $0.74/月
```

### その他のサービス
- **ECR**: $0.10/月（1GBまで無料）
- **S3**: $0.10/月（チャート画像保存）
- **CloudWatch**: $0.50/月（ログ・メトリクス）
- **SNS**: $0.10/月（アラート通知）

**総コスト: 約$1.54/月**

## 運用・監視

### 1. ログ確認
```bash
# リアルタイムログ監視
aws logs tail /ecs/fx-analyzer-prod --follow

# 特定期間のログ
aws logs filter-log-events \
    --log-group-name /ecs/fx-analyzer-prod \
    --start-time $(date -d "1 hour ago" +%s)000
```

### 2. 手動実行
```bash
# タスクを手動実行
aws ecs run-task \
    --cluster fx-analyzer-cluster-prod \
    --task-definition fx-analyzer-prod \
    --launch-type FARGATE \
    --network-configuration 'awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}'
```

### 3. メトリクス確認
```bash
# タスク実行状況
aws ecs describe-clusters --clusters fx-analyzer-cluster-prod

# タスク履歴
aws ecs list-tasks --cluster fx-analyzer-cluster-prod
```

## トラブルシューティング

### 1. よくある問題

**Docker Build失敗**
```bash
# 依存関係エラーの場合
docker build --no-cache -t fx-analyzer .
```

**ECRプッシュ失敗**
```bash
# 認証確認
aws ecr get-login-password --region ap-northeast-1
```

**タスク起動失敗**
```bash
# タスク詳細確認
aws ecs describe-tasks --cluster fx-analyzer-cluster-prod --tasks [task-arn]
```

### 2. 設定変更

**スケジュール変更**
```bash
# template-ecs.yamlのcron式を変更してre-deploy
ScheduleExpression: "cron(0 1 * * ? *)"  # UTC 1:00 = JST 10:00 AM
```

**リソース変更**
```bash
# CPU/メモリを増加
Cpu: 2048  # 2 vCPU
Memory: 4096  # 4GB
```

## Lambda vs ECS Fargate 比較

| 項目 | Lambda | ECS Fargate |
|------|--------|-------------|
| チャート品質 | ❌ 制限あり | ✅ 高品質 |
| 実行時間 | ❌ 15分制限 | ✅ 制限なし |
| コスト | ✅ $2-3/月 | ✅ $1.5/月 |
| 管理複雑さ | ✅ 簡単 | 🔄 中程度 |
| スケーラビリティ | ✅ 自動 | ✅ 自動 |
| 依存関係 | ❌ 制限あり | ✅ 自由 |

## まとめ

ECS Fargateソリューションにより：
- ✅ 高品質チャート生成維持
- ✅ Lambdaより低コスト
- ✅ 完全なPythonライブラリサポート
- ✅ 定時実行・監視機能
- ✅ スケーラブルなアーキテクチャ

最高品質のFXチャート分析システムが実現できます。