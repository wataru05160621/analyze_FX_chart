# 本番運用チェックリスト

本番運用開始前に完了すべき項目の詳細チェックリストです。

## 🔥 高優先度（本番開始前必須）

### ✅ 1. APIキーの取得と設定

#### OpenAI APIキー
- [ ] OpenAI Platformアカウント作成
- [ ] 支払い方法の設定（クレジットカード登録）
- [ ] APIキーの生成
- [ ] 使用量制限の設定（月額$50-100推奨）
- [ ] キーの安全な保存

**手順:**
```bash
# 1. https://platform.openai.com/ でアカウント作成
# 2. Billing → Payment methods でカード登録
# 3. API keys → Create new secret key
# 4. キーをコピーして安全に保存
```

#### Notion APIキー
- [ ] Notion DevelopersでIntegration作成
- [ ] データベースの作成・設定
- [ ] Integration権限の設定
- [ ] データベースとIntegrationの接続

**手順:**
```bash
# 1. https://www.notion.so/my-integrations でIntegration作成
# 2. Notionでデータベース作成
# 3. データベースページで「...」→ Add connections → Integration選択
```

#### Trading View設定
- [ ] 普段使用しているチャートURLの特定
- [ ] URLが正しく動作することを確認

### ✅ 2. 本番環境での動作確認

#### ローカル環境テスト
```bash
# 2.1 システム診断
source venv/bin/activate
python debug_tool.py

# 期待結果: すべてのテストがPASS
```

#### 実APIを使用したテスト
```bash
# 2.2 .envファイルに実際のAPIキーを設定
cp .env.example .env
# 編集: OPENAI_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID

# 2.3 1回実行テスト
python -m src.main --debug

# 期待結果: 
# - Trading Viewスクリーンショット取得成功
# - OpenAI API分析成功
# - Notion保存成功
```

### ✅ 3. AWS環境のセットアップ

#### AWS CLI設定
- [ ] AWSアカウント作成
- [ ] IAMユーザー作成（必要な権限付与）
- [ ] AWS CLIインストール・設定
- [ ] 権限テスト

```bash
# 3.1 AWS CLIインストール
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# 3.2 認証設定
aws configure

# 3.3 権限確認
aws sts get-caller-identity
```

#### S3バケット作成
- [ ] 画像保存用バケット作成
- [ ] 適切な権限設定
- [ ] ライフサイクルポリシー設定

```bash
# 3.4 S3バケット作成
aws s3 mb s3://fx-analyzer-images-prod --region ap-northeast-1

# 3.5 パブリックアクセスブロック
aws s3api put-public-access-block \
    --bucket fx-analyzer-images-prod \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

#### Lambda関数デプロイ
- [ ] SAM CLIまたはServerless CLIインストール
- [ ] 環境変数設定
- [ ] デプロイ実行
- [ ] テスト実行

```bash
# 3.6 環境変数設定
export OPENAI_API_KEY="your_actual_key"
export NOTION_API_KEY="your_actual_key"
export NOTION_DATABASE_ID="your_actual_id"

# 3.7 デプロイ
chmod +x deploy.sh
./deploy.sh prod sam

# 3.8 テスト実行
aws lambda invoke \
    --function-name fx-analyzer-test-prod \
    response.json && cat response.json
```

## 📊 中優先度（運用開始後1週間以内）

### ✅ 4. 監視・アラート設定

#### CloudWatch監視
- [ ] Lambda関数のメトリクス確認
- [ ] ログ保存期間設定
- [ ] エラーアラーム設定

```bash
# 4.1 エラーアラーム設定
aws cloudwatch put-metric-alarm \
    --alarm-name "fx-analyzer-errors-prod" \
    --alarm-description "FX Analyzer Lambda errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --dimensions Name=FunctionName,Value=fx-analyzer-prod
```

#### 通知設定
- [ ] SNSトピック作成
- [ ] メール通知設定
- [ ] Slack通知設定（オプション）

### ✅ 5. バックアップ・災害復旧

#### データバックアップ
- [ ] Notionデータのエクスポート手順
- [ ] S3バケットのバージョニング有効化
- [ ] コードリポジトリのバックアップ

#### 災害復旧計画
- [ ] 復旧手順書の作成
- [ ] 代替実行環境の準備
- [ ] データ復旧テスト

## 📝 低優先度（運用安定後）

### ✅ 6. 運用手順書

#### 日常運用
- [ ] 日次チェック項目
- [ ] 週次メンテナンス
- [ ] 月次レポート

#### トラブルシューティング
- [ ] よくある問題と解決方法
- [ ] エスカレーション手順
- [ ] 緊急連絡先

## 📋 本番運用開始手順

### Phase 1: 準備完了確認（開始前）
```bash
# 全項目チェック
python debug_tool.py  # すべてPASS確認
aws lambda invoke --function-name fx-analyzer-test-prod response.json  # 成功確認
```

### Phase 2: 段階的運用開始

#### 1日目: 手動実行
```bash
# 午前8時に手動実行
aws lambda invoke --function-name fx-analyzer-prod response.json

# 結果確認
# - Notionに新しいページが作成されているか
# - S3に画像がアップロードされているか
# - エラーが発生していないか
```

#### 2-3日目: 一部自動実行
- 1日1回の自動実行に設定
- 結果を毎日手動確認

#### 1週間後: 完全自動実行
- 1日3回の完全自動実行開始
- 監視・アラート体制確立

### Phase 3: 運用最適化（1ヶ月後）
- パフォーマンスチューニング
- コスト最適化
- 機能拡張検討

## 💰 コスト見積もり

### 月間コスト（1日3回実行）
- **OpenAI API (GPT-4)**: $30-50
- **AWS Lambda**: $5-10
- **AWS S3**: $2-5
- **Notion API**: 無料（制限内）
- **その他AWS料金**: $3-7

**合計**: 約$40-70/月

### コスト最適化方法
- OpenAI APIの使用量監視
- S3ライフサイクルポリシーの活用
- Lambda実行時間の最適化

## 🚨 重要な注意事項

### セキュリティ
1. **APIキーの管理**
   - 絶対にコードに埋め込まない
   - 定期的にローテーション
   - AWS Secrets Manager使用を検討

2. **アクセス制御**
   - IAMポリシーで最小権限
   - MFA有効化
   - CloudTrailで操作ログ記録

### 可用性
1. **冗長化**
   - 複数リージョンでの実行（オプション）
   - 代替実行環境の準備

2. **監視**
   - 24時間監視体制
   - 自動復旧機能

### コンプライアンス
1. **データ保護**
   - 個人情報の適切な取り扱い
   - データ保存期間の管理

2. **利用規約遵守**
   - Trading Viewの利用規約
   - OpenAI・Notionの利用規約

## ✅ 最終チェック

本番運用開始前に以下をすべて確認：

- [ ] すべてのAPIキーが正常に動作
- [ ] AWS環境が正しく設定
- [ ] テスト実行が成功
- [ ] 監視・アラートが設定
- [ ] バックアップ計画が策定
- [ ] 緊急時対応手順が明確
- [ ] コスト監視が設定
- [ ] セキュリティチェック完了

**すべてチェック完了後、本番運用を開始してください！** 🚀