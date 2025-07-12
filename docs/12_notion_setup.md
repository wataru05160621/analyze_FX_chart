# Notion API セットアップガイド

## 1. Notion Integration の作成

1. [Notion Developers](https://www.notion.so/my-integrations) にアクセス
2. 「New integration」をクリック
3. 以下を設定：
   - Name: `FX Chart Analyzer`
   - Associated workspace: あなたのワークスペース
   - Capabilities: 
     - Read content ✓
     - Update content ✓
     - Insert content ✓

4. 「Submit」をクリック
5. 「Internal Integration Token」をコピー → `.env`の`NOTION_API_KEY`に設定

## 2. データベースの作成

### 方法1: 手動作成（推奨）

1. Notionで新しいページを作成
2. `/database`と入力して「Database - Full page」を選択
3. データベース名を「FX分析結果」に設定
4. 以下のプロパティを追加：

| プロパティ名 | タイプ | オプション |
|------------|-------|----------|
| Name | Title | - |
| Date | Date | - |
| Status | Select | 分析中, 完了, エラー |
| Currency | Select | USD/JPY, EUR/USD, GBP/USD |
| Timeframe | Multi-select | 5分足, 1時間足, 4時間足, 日足 |

### 方法2: 自動作成

```python
from src.notion_writer import NotionWriter

# 親ページのIDを指定
parent_page_id = "your_parent_page_id"

writer = NotionWriter()
database_id = writer.create_database(parent_page_id)
print(f"データベースID: {database_id}")
```

## 3. データベースとIntegrationの接続

1. 作成したデータベースページを開く
2. 右上の「...」メニューをクリック
3. 「Add connections」を選択
4. 「FX Chart Analyzer」を検索して選択
5. 「Confirm」をクリック

## 4. データベースIDの取得

1. データベースページのURLをコピー
   ```
   https://www.notion.so/workspace/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
   ```

2. `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`の部分がデータベースID
3. `.env`の`NOTION_DATABASE_ID`に設定

## 5. 画像アップロードの設定

Notion APIは直接の画像アップロードをサポートしていないため、以下のいずれかの方法を選択：

### オプション1: Cloudinary（推奨）

1. [Cloudinary](https://cloudinary.com/)でアカウント作成
2. APIキーを取得
3. `.env`に追加：
   ```
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

### オプション2: Imgur

1. [Imgur API](https://api.imgur.com/)でアプリケーション登録
2. Client IDを取得
3. `.env`に追加：
   ```
   IMGUR_CLIENT_ID=your_client_id
   ```

### オプション3: AWS S3

1. S3バケットを作成
2. IAMユーザーを作成してアクセスキーを取得
3. `.env`に追加：
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_S3_BUCKET=your_bucket_name
   ```

## 6. テスト実行

```python
from src.notion_writer import NotionWriter
from pathlib import Path

writer = NotionWriter()

# テストデータ
test_images = {
    "5min": Path("test_5min.png"),
    "1hour": Path("test_1hour.png")
}

# ページ作成テスト
page_id = writer.create_analysis_page(
    title="テスト分析_20240626",
    analysis="これはテスト分析結果です。",
    chart_images=test_images
)

print(f"作成されたページID: {page_id}")
```

## トラブルシューティング

### "unauthorized" エラー
- IntegrationがデータベースにアクセスできるようにConnectionを追加したか確認

### "object_not_found" エラー
- データベースIDが正しいか確認
- データベースが削除されていないか確認

### 画像が表示されない
- 画像URLが公開アクセス可能か確認
- 画像サイズが大きすぎないか確認（推奨: 5MB以下）