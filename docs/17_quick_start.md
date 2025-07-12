# 🚀 クイックスタートガイド

最短で本番運用を開始するためのステップバイステップガイドです。

## ⏱️ 所要時間: 約30-60分

## 📋 事前準備

必要なアカウント：
- [ ] OpenAI Platform アカウント
- [ ] Notion アカウント
- [ ] AWS アカウント

## 🎯 ステップ1: APIキーの取得（15分）

### 1.1 OpenAI APIキー取得
```bash
# 1. https://platform.openai.com/ にアクセス
# 2. アカウント作成・ログイン
# 3. Billing → Add payment method でクレジットカード登録
# 4. API Keys → Create new secret key
# 5. キーをコピー（sk-proj-で始まる文字列）
```

### 1.2 Notion APIキー取得
```bash
# 1. https://www.notion.so/my-integrations にアクセス
# 2. New integration → 名前入力「FX Chart Analyzer」
# 3. Submit → Internal Integration Token をコピー
# 4. Notionでデータベース作成（テンプレート使用可）
# 5. データベースページで「...」→ Add connections → 作成したIntegration選択
# 6. データベースのURLからIDを取得
```

## 🎯 ステップ2: 環境設定（10分）

### 2.1 プロジェクト設定
```bash
# リポジトリクローン
git clone https://github.com/wataru05160621/analyze_FX_chart.git
cd analyze_FX_chart

# 自動セットアップ実行
chmod +x setup.sh
./setup.sh
```

### 2.2 環境変数設定
```bash
# .envファイル編集
cp .env.example .env
nano .env
```

**.envファイルに以下を設定:**
```env
# 必須項目
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# オプション項目
TRADINGVIEW_CUSTOM_URL=https://jp.tradingview.com/chart/xxxxx/
USE_WEB_CHATGPT=false
AWS_S3_BUCKET=fx-analyzer-screenshots-prod
```

## 🎯 ステップ3: ローカルテスト（10分）

### 3.1 システム診断
```bash
source venv/bin/activate
python debug_tool.py
```

**期待結果:** すべてのテストがPASS

### 3.2 1回実行テスト
```bash
python -m src.main --debug
```

**期待結果:** 
- ✅ チャートスクリーンショット取得
- ✅ AI分析実行
- ✅ Notion保存成功

## 🎯 ステップ4: AWS設定（15分）

### 4.1 AWS CLI設定
```bash
# AWS CLIインストール（macOS）
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# 認証設定
aws configure
# Access Key ID: YOUR_ACCESS_KEY
# Secret Access Key: YOUR_SECRET_KEY  
# Default region: ap-northeast-1
# Default output format: json
```

### 4.2 S3バケット作成
```bash
# バケット作成
aws s3 mb s3://fx-analyzer-screenshots-prod --region ap-northeast-1

# セキュリティ設定
aws s3api put-public-access-block \
    --bucket fx-analyzer-screenshots-prod \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

## 🎯 ステップ5: AWS Lambda デプロイ（10分）

### 5.1 環境変数設定
```bash
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export NOTION_API_KEY="secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export NOTION_DATABASE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 5.2 デプロイ実行
```bash
# SAM CLIインストール（推奨）
brew install aws/tap/aws-sam-cli

# デプロイ
chmod +x deploy.sh
./deploy.sh prod sam
```

### 5.3 本番テスト
```bash
# Lambda関数テスト
aws lambda invoke \
    --function-name fx-analyzer-test-prod \
    response.json

# 結果確認
cat response.json
```

## 🎯 ステップ6: 運用開始

### 6.1 自動実行確認
```bash
# 次回実行時刻の確認
aws events list-rules --name-prefix fx-analyzer

# ログ監視
aws logs tail /aws/lambda/fx-analyzer-prod --follow
```

### 6.2 結果確認先

1. **Notion**: 新しい分析ページが作成される
2. **S3バケット**: チャート画像がアップロードされる
3. **CloudWatch Logs**: 実行ログが記録される

## 🚨 トラブルシューティング

### よくある問題

#### 1. OpenAI API エラー
```
Error: 401 Unauthorized
→ APIキーを再確認、請求設定を確認
```

#### 2. Notion API エラー
```
Error: object_not_found  
→ データベースIDとIntegration接続を確認
```

#### 3. AWS エラー
```
Error: NoCredentialsError
→ aws configure で認証情報を再設定
```

#### 4. デプロイエラー
```
Error: StackName already exists
→ 既存スタックを削除: aws cloudformation delete-stack --stack-name fx-analyzer-prod
```

### デバッグコマンド
```bash
# 詳細ログでの実行
python -m src.main --debug

# システム診断
python debug_tool.py

# AWS権限確認
aws sts get-caller-identity

# Lambda関数の直接実行
aws lambda invoke --function-name fx-analyzer-prod output.json
```

## ✅ 成功チェックリスト

運用開始後、以下を確認してください：

### 即座に確認
- [ ] Lambda関数が正常にデプロイされた
- [ ] テスト実行が成功した
- [ ] Notionに分析結果が保存された
- [ ] S3に画像がアップロードされた

### 24時間後に確認
- [ ] 自動実行が正常に動作している（日本時間8:00, 15:00, 21:00）
- [ ] エラーが発生していない
- [ ] API使用量が想定範囲内

### 1週間後に確認
- [ ] 継続的に分析が実行されている
- [ ] Notionデータベースに新しいエントリが蓄積されている
- [ ] AWSコストが予算内

## 📞 サポート

### 技術的な問題
1. GitHubのIssuesページで質問
2. ログファイル（`logs/fx_analysis.log`）を確認
3. CloudWatch Logsを確認

### 緊急時対応
```bash
# 自動実行を一時停止
aws events disable-rule --name fx-analyzer-morning-prod
aws events disable-rule --name fx-analyzer-afternoon-prod  
aws events disable-rule --name fx-analyzer-evening-prod

# 自動実行を再開
aws events enable-rule --name fx-analyzer-morning-prod
aws events enable-rule --name fx-analyzer-afternoon-prod
aws events enable-rule --name fx-analyzer-evening-prod
```

## 🎉 完了！

**おめでとうございます！** FXチャート自動分析システムが本番運用を開始しました。

**日本時間の8:00、15:00、21:00に自動でTrading Viewのチャートを分析し、結果をNotionに保存します。**

---

**💡 次のステップ:**
- [監視設定](aws_setup.md#監視とアラート)
- [コスト最適化](production_checklist.md#コスト見積もり)
- [機能拡張](../README.md#今後の拡張予定)