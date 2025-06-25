# FXチャート自動分析システム

Trading ViewのチャートをChatGPTプロジェクトで分析し、Notionに保存するシステムです。

## 機能

1. **Trading Viewチャート取得**
   - あなたが普段使用しているチャートのURLを指定可能
   - 5分足と1時間足のスクリーンショットを自動取得

2. **ChatGPTプロジェクト連携**
   - Web版ChatGPTの既存プロジェクトにアクセス
   - プロジェクトファイル（プライスアクションの原則.pdf）を活用した分析
   - API版への切り替えも可能

3. **Notion自動保存**
   - 分析結果とチャート画像を自動でNotionに保存
   - 日時付きで整理

## セットアップ

### 1. 環境設定

`.env`ファイルを作成し、以下の情報を設定：

```bash
# Trading View設定
TRADINGVIEW_CUSTOM_URL=https://jp.tradingview.com/chart/xxxxx/  # あなたのチャートURL

# ChatGPT Web設定
CHATGPT_EMAIL=your_email@example.com
CHATGPT_PASSWORD=your_password
CHATGPT_PROJECT_NAME=FXチャート分析  # プロジェクト名

# Notion設定
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id

# 分析モード
USE_WEB_CHATGPT=true  # Web版を使用する場合
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. プロジェクトファイルの配置

`doc/プライスアクションの原則.pdf`が既に配置されています。

## 使用方法

### 手動実行

```bash
python -m src.main
```

### 定時実行の設定

cronやタスクスケジューラで以下のコマンドを設定：

```bash
0 9,15,21 * * * cd /path/to/project && python -m src.main
```

## カスタマイズ

### チャートURL

`.env`の`TRADINGVIEW_CUSTOM_URL`にあなたが普段使用しているチャートのURLを設定してください。

### 時間足の変更

`src/config.py`の`TIMEFRAMES`を編集：

```python
TIMEFRAMES = {
    "5min": "5",
    "15min": "15",  # 15分足を追加
    "1hour": "60"
}
```

### 分析プロンプト

`src/config.py`の`ANALYSIS_PROMPT`を編集して、分析内容をカスタマイズできます。

## トラブルシューティング

### ChatGPTログインエラー

- 2段階認証を使用している場合は、一時的に無効化が必要
- セッションが切れた場合は、ブラウザでログインし直してください

### スクリーンショット取得エラー

- Trading ViewのUIが変更された場合、セレクターの更新が必要
- `headless=False`に設定してデバッグ

## 今後の拡張

- ブログへの自動投稿機能
- 複数通貨ペア対応
- アラート機能の追加