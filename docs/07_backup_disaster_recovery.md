# バックアップ・災害復旧計画

## 概要

FXチャート分析システムの継続的運用のためのバックアップ・災害復旧計画です。

## バックアップ対象

### 1. **重要データ**
- **Notionデータベース**: 分析結果（自動バックアップ）
- **チャート画像**: S3バケット内（30日保存）
- **分析履歴**: CloudWatchログ（14日保存）
- **設定情報**: Secrets Manager（バージョン管理）

### 2. **システム設定**
- **CloudFormationテンプレート**: GitHubリポジトリ
- **アプリケーションコード**: GitHubリポジトリ
- **Dockerイメージ**: ECRリポジトリ（10イメージ保存）
- **環境変数**: Secrets Manager

## バックアップ戦略

### 1. **自動バックアップ**

#### S3チャート画像
```yaml
# template-ecs.yamlに設定済み
LifecycleConfiguration:
  Rules:
    - Id: DeleteOldCharts
      Status: Enabled
      ExpirationInDays: 30  # 30日間保存
```

#### ECRイメージバックアップ
```yaml
# 自動的に最新10イメージを保持
LifecyclePolicy:
  rules:
    - rulePriority: 1
      description: "Keep last 10 images"
      selection:
        countType: "imageCountMoreThan"
        countNumber: 10
      action:
        type: "expire"
```

#### CloudWatchログ
```yaml
# 14日間のログ保存
LogGroup:
  RetentionInDays: 14
```

### 2. **手動バックアップ**

#### 重要設定のエクスポート
```bash
# Secrets Managerの値をエクスポート
aws secretsmanager get-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --query SecretString --output text > backup-secrets.json

# CloudFormationテンプレートをエクスポート
aws cloudformation get-template \
    --stack-name fx-analyzer-ecs-prod \
    --query TemplateBody > backup-template.json
```

#### Notionデータのバックアップ
```python
# notion_backup.py
import os
from notion_client import Client

def backup_notion_database():
    """Notionデータベースをバックアップ"""
    notion = Client(auth=os.environ["NOTION_API_KEY"])
    database_id = os.environ["NOTION_DATABASE_ID"]
    
    # 全ページを取得
    pages = notion.databases.query(database_id=database_id)
    
    # JSONファイルに保存
    with open(f"notion_backup_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
```

## 災害復旧手順

### 1. **完全復旧シナリオ**

#### ステップ1: 基盤の復旧
```bash
# 1. GitHubからコードを取得
git clone https://github.com/your-repo/fx-analyzer.git
cd fx-analyzer

# 2. 環境変数を設定
cp backup-secrets.json .env

# 3. CloudFormationスタックをデプロイ
./deploy-ecs.sh
```

#### ステップ2: データの復旧
```bash
# 1. Secrets Managerを復元
aws secretsmanager put-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --secret-string file://backup-secrets.json

# 2. Dockerイメージを再ビルド・プッシュ
docker build -t fx-analyzer .
docker tag fx-analyzer:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest
```

#### ステップ3: 動作確認
```bash
# 1. 手動タスク実行でテスト
aws ecs run-task \
    --cluster fx-analyzer-cluster-prod \
    --task-definition fx-analyzer-prod \
    --launch-type FARGATE

# 2. ログでエラーがないことを確認
aws logs tail /ecs/fx-analyzer-prod --follow

# 3. Notionに結果が書き込まれることを確認
```

### 2. **部分復旧シナリオ**

#### ECSタスクのみ復旧
```bash
# タスク定義を最新イメージで更新
aws ecs update-service \
    --cluster fx-analyzer-cluster-prod \
    --service fx-analyzer-service \
    --force-new-deployment
```

#### Secrets Managerのみ復旧
```bash
# バックアップから復元
aws secretsmanager put-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --secret-string file://backup-secrets.json
```

## 監視・アラート

### 1. **システム監視**
```yaml
# CloudWatchアラーム（設定済み）
TaskFailureAlarm:
  MetricName: TaskStoppedReason
  Namespace: AWS/ECS
  Threshold: 1
  AlarmActions:
    - !Ref AlertTopic
```

### 2. **データ整合性チェック**
```python
# データ整合性チェックスクリプト
def check_data_integrity():
    """データの整合性をチェック"""
    # 1. 最新のNotionページを確認
    # 2. S3のチャート画像を確認  
    # 3. ログエラーを確認
    # 4. 異常があればSlack/メール通知
```

### 3. **定期ヘルスチェック**
```bash
# 週次ヘルスチェックスクリプト
#!/bin/bash
# weekly_health_check.sh

# 1. ECSクラスター状態確認
aws ecs describe-clusters --clusters fx-analyzer-cluster-prod

# 2. 最新の実行ログ確認
aws logs filter-log-events \
    --log-group-name /ecs/fx-analyzer-prod \
    --start-time $(date -d "7 days ago" +%s)000 \
    --filter-pattern "ERROR"

# 3. Notion書き込み状況確認
# 4. S3容量使用状況確認
aws s3 ls s3://fx-analyzer-charts-ecs-prod-455931011903 --summarize --human-readable --recursive
```

## RPO/RTO目標

### **Recovery Point Objective (RPO)**
- **チャート画像**: 24時間以内
- **分析結果**: 1時間以内（Notion同期）
- **システム設定**: 即座（Git管理）

### **Recovery Time Objective (RTO)**
- **完全復旧**: 2時間以内
- **部分復旧**: 30分以内
- **緊急対応**: 15分以内

## 緊急連絡先・手順

### 1. **障害エスカレーション**
```
Level 1: CloudWatchアラーム → SNS → メール通知
Level 2: 連続失敗 → Slack通知
Level 3: 長期停止 → 電話連絡
```

### 2. **緊急時チェックリスト**
```
□ CloudWatchでエラーログを確認
□ ECSタスクの実行状況を確認
□ Secrets Managerの設定を確認
□ Notion API接続を確認
□ 手動実行でテスト
□ 必要に応じて再デプロイ
```

## 定期メンテナンス

### 1. **月次作業**
- [ ] バックアップデータの整合性確認
- [ ] 不要なログ・画像の削除確認
- [ ] セキュリティパッチの適用
- [ ] コスト使用状況の確認

### 2. **四半期作業**
- [ ] 災害復旧手順のテスト実行
- [ ] APIキーの更新検討
- [ ] システム性能の見直し
- [ ] バックアップ戦略の見直し

### 3. **年次作業**
- [ ] 全システムの復旧テスト
- [ ] セキュリティ監査
- [ ] アーキテクチャの見直し
- [ ] コスト最適化の検討

## まとめ

この災害復旧計画により：
- ✅ **データ保護**: 重要データの自動バックアップ
- ✅ **迅速復旧**: 2時間以内の完全復旧
- ✅ **監視体制**: 24/7自動監視とアラート
- ✅ **定期メンテナンス**: 継続的な品質保証

システムの可用性と信頼性を最大化し、ビジネス継続性を確保します。