# 本番環境テストガイド

本番環境でFX分析システムをテストするための手順です。

## 1. 本番用環境変数の設定

`.env`ファイルを実際のAPIキーで更新してください：

```bash
# OpenAI API設定（必須）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Notion API設定（必須）
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Trading View設定
TRADINGVIEW_CUSTOM_URL=https://jp.tradingview.com/chart/xxxxx/  # あなたのチャートURL

# ChatGPT Web設定（Web版を使用する場合）
CHATGPT_EMAIL=your_email@example.com
CHATGPT_PASSWORD=your_password
CHATGPT_PROJECT_NAME=FXチャート分析

# 分析モード設定
USE_WEB_CHATGPT=false  # 本番環境ではfalse推奨（API版）

# 画像アップロード設定（AWS S3）
AWS_S3_BUCKET=fx-analyzer-screenshots-prod  # 実際のバケット名
AWS_REGION=ap-northeast-1
```

## 2. API キーの取得方法

### OpenAI API キー

1. [OpenAI Platform](https://platform.openai.com/) にログイン
2. 右上のアカウントメニュー → "View API Keys"
3. "Create new secret key" をクリック
4. 生成されたキーをコピー（**重要**: 一度しか表示されません）

### Notion API キー

1. [Notion Developers](https://www.notion.so/my-integrations) にアクセス
2. "New integration" をクリック
3. 名前を設定（例: "FX Chart Analyzer"）
4. ワークスペースを選択
5. 権限設定:
   - Read content ✓
   - Update content ✓
   - Insert content ✓
6. "Submit" をクリック
7. "Internal Integration Token" をコピー

### Notion データベース ID

1. Notionでデータベースページを開く
2. URLから32文字のIDを取得:
   ```
   https://www.notion.so/workspace/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=yyyyyyyy
   ```
   `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` の部分がデータベースID

## 3. AWS S3の設定

### バケットの作成

```bash
# S3バケットを作成
aws s3 mb s3://fx-analyzer-screenshots-prod --region ap-northeast-1

# パブリックアクセスをブロック
aws s3api put-public-access-block \
    --bucket fx-analyzer-screenshots-prod \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### IAMポリシーの設定

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::fx-analyzer-screenshots-prod/*"
        }
    ]
}
```

## 4. システムテストの実行

### ステップ1: 依存関係の確認

```bash
source venv/bin/activate
python debug_tool.py
```

期待される結果：
- ✅ 設定テスト: PASS
- ✅ インポートテスト: PASS
- ✅ 依存関係テスト: PASS
- ✅ AWS S3テスト: PASS
- ✅ スクレイパーテスト: PASS
- ✅ ドライラン: PASS

### ステップ2: 1回実行テスト

```bash
# デバッグモードで実行
python -m src.main --debug
```

このテストでは以下が確認されます：
1. Trading Viewからのスクリーンショット取得
2. OpenAI APIでの分析
3. AWS S3への画像アップロード
4. Notionへの結果保存

### ステップ3: スケジューラーテスト

```bash
# スケジューラーの1回実行
python run_scheduler.py --once
```

## 5. 本番環境での注意事項

### コスト管理

- **OpenAI API**: gpt-4の使用料金に注意
- **AWS S3**: ストレージとデータ転送料金
- **Notion API**: 無料プランの制限確認

### エラー監視

```bash
# ログファイルの監視
tail -f logs/fx_analysis.log

# エラーログの確認
grep "ERROR" logs/fx_analysis.log
```

### セキュリティ

1. **APIキーの保護**
   - `.env`ファイルを`.gitignore`に追加済み
   - 本番環境では環境変数またはAWS Secrets Managerを使用

2. **アクセス制御**
   - AWS IAMで最小権限の原則を適用
   - Notion Integrationの権限を最小限に設定

## 6. トラブルシューティング

### よくある問題

1. **OpenAI API エラー**
   ```
   Error: 401 Unauthorized
   → APIキーを確認
   ```

2. **Notion API エラー**
   ```
   Error: object_not_found
   → データベースIDとIntegration接続を確認
   ```

3. **AWS S3 エラー**
   ```
   Error: NoCredentialsError
   → AWS CLIの設定を確認: aws configure
   ```

4. **Trading View エラー**
   ```
   Error: Timeout
   → ネットワーク接続とTradingViewのURLを確認
   ```

### デバッグ方法

```bash
# 詳細ログでの実行
python -m src.main --debug

# 特定のコンポーネントのテスト
python -c "
from src.tradingview_scraper import TradingViewScraper
import asyncio

async def test():
    scraper = TradingViewScraper()
    await scraper.setup()
    await scraper.close()

asyncio.run(test())
"
```

## 7. 本番デプロイメント

### ローカル実行

```bash
# 定時実行の開始
python run_scheduler.py
```

### AWS Lambda デプロイ

```bash
# 環境変数の設定
export OPENAI_API_KEY="your_key"
export NOTION_API_KEY="your_key"
export NOTION_DATABASE_ID="your_id"

# デプロイ実行
chmod +x deploy.sh
./deploy.sh prod sam
```

## 8. 本番運用開始後の監視

### 日次チェック項目

1. **Notionデータベース**: 新しい分析結果が追加されているか
2. **S3バケット**: チャート画像が正常にアップロードされているか
3. **ログファイル**: エラーが発生していないか

### 週次チェック項目

1. **API使用量**: OpenAIとNotionの使用量確認
2. **AWSコスト**: 予想範囲内かチェック
3. **ディスク容量**: ログファイルのサイズ確認

### 推奨アラート設定

```bash
# CloudWatchアラーム（AWS Lambda使用時）
aws cloudwatch put-metric-alarm \
    --alarm-name "fx-analyzer-errors" \
    --alarm-description "FX Analyzer errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold
```