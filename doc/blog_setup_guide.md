# WordPress + X 自動投稿セットアップガイド

## 概要

このガイドでは、FX分析結果を毎日8:00にWordPressブログとX（Twitter）に自動投稿する機能のセットアップ方法を説明します。

## 前提条件

- WordPress（ConoHa WING推奨）が設定済み
- WordPress管理者アカウント
- X（Twitter）開発者アカウント

## 1. WordPress設定

### 1.1 アプリケーションパスワードの作成

1. WordPress管理画面にログイン
2. 「ユーザー」→「プロフィール」に移動
3. 「アプリケーションパスワード」セクションまでスクロール
4. 新しいアプリケーションパスワード名を入力（例：`FX-Analysis-Bot`）
5. 「新しいアプリケーションパスワードを追加」をクリック
6. 生成されたパスワードをコピー（スペースは削除）

### 1.2 REST APIの有効化確認

ブラウザで以下のURLにアクセスしてJSONが表示されることを確認：

```
https://your-domain.com/wp-json/wp/v2/posts
```

## 2. X（Twitter）API設定

### 2.1 開発者アカウントの作成

1. [Twitter Developer Portal](https://developer.twitter.com/)にアクセス
2. 開発者アカウントを申請（承認に数日かかる場合があります）

### 2.2 アプリケーションの作成

1. Developer Portalにログイン
2. 「Projects & Apps」→「Overview」
3. 「Create App」をクリック
4. アプリ名を入力（例：`FX-Analysis-Bot`）

### 2.3 API認証情報の取得

1. アプリの「Keys and tokens」タブに移動
2. 以下の情報を取得：
   - API Key (Consumer Key)
   - API Key Secret (Consumer Secret)
   - Access Token
   - Access Token Secret

### 2.4 権限設定

1. 「Settings」→「User authentication settings」
2. 「App permissions」を「Read and write」に設定
3. 保存

## 3. 環境変数の設定

### 3.1 ローカル開発環境（.env）

`.env`ファイルに以下を追加：

```bash
# WordPress設定
WORDPRESS_URL=https://your-domain.com
WORDPRESS_USERNAME=your_wordpress_username
WORDPRESS_PASSWORD=生成したアプリケーションパスワード

# X (Twitter) API設定
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# ブログ投稿設定
ENABLE_BLOG_POSTING=true  # 有効化
BLOG_POST_HOUR=8  # JST 8:00
```

### 3.2 AWS Secrets Manager設定

既存のシークレットに以下のキーを追加：

```bash
# AWS CLIで更新
aws secretsmanager get-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --query SecretString \
    --output text > current_secrets.json

# current_secrets.jsonを編集して以下を追加
{
    ...既存の設定...,
    "WORDPRESS_URL": "https://your-domain.com",
    "WORDPRESS_USERNAME": "your_username",
    "WORDPRESS_PASSWORD": "your_app_password",
    "TWITTER_API_KEY": "your_api_key",
    "TWITTER_API_SECRET": "your_api_secret",
    "TWITTER_ACCESS_TOKEN": "your_token",
    "TWITTER_ACCESS_TOKEN_SECRET": "your_token_secret",
    "ENABLE_BLOG_POSTING": "true",
    "BLOG_POST_HOUR": "8"
}

# シークレットを更新
aws secretsmanager update-secret \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --secret-string file://current_secrets.json
```

## 4. タスク定義の更新

### 4.1 新しい環境変数をタスク定義に追加

`full-v2-taskdef.json`の`secrets`セクションに追加：

```json
{
    "name": "WORDPRESS_URL",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:WORDPRESS_URL::"
},
{
    "name": "WORDPRESS_USERNAME",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:WORDPRESS_USERNAME::"
},
{
    "name": "WORDPRESS_PASSWORD",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:WORDPRESS_PASSWORD::"
},
{
    "name": "TWITTER_API_KEY",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:TWITTER_API_KEY::"
},
{
    "name": "TWITTER_API_SECRET",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:TWITTER_API_SECRET::"
},
{
    "name": "TWITTER_ACCESS_TOKEN",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:TWITTER_ACCESS_TOKEN::"
},
{
    "name": "TWITTER_ACCESS_TOKEN_SECRET",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:TWITTER_ACCESS_TOKEN_SECRET::"
},
{
    "name": "ENABLE_BLOG_POSTING",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:ENABLE_BLOG_POSTING::"
},
{
    "name": "BLOG_POST_HOUR",
    "valueFrom": "arn:aws:secretsmanager:ap-northeast-1:455931011903:secret:fx-analyzer-ecs-secrets-prod:BLOG_POST_HOUR::"
}
```

### 4.2 新しいDockerイメージをビルド・プッシュ

```bash
# Dockerイメージをビルド
docker build -f Dockerfile.full -t fx-analyzer-full --platform linux/amd64 .

# タグ付け（blog-v1タグ）
docker tag fx-analyzer-full:latest 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/fx-analyzer-prod:blog-v1

# ECRにプッシュ
docker push 455931011903.dkr.ecr.ap-northeast-1.amazonaws.com/fx-analyzer-prod:blog-v1
```

### 4.3 タスク定義を更新

```bash
# タスク定義のimageを更新
sed -i 's/ema-trend-follow-v1/blog-v1/g' full-v2-taskdef.json

# タスク定義を登録
aws ecs register-task-definition --cli-input-json file://full-v2-taskdef.json
```

## 5. デプロイと確認

### 5.1 CloudFormationスタックの更新

```bash
# 新しいタスク定義でスタックを更新
sam deploy --template-file template-ecs.yaml \
    --stack-name fx-analyzer-ecs-prod \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Environment=prod
```

### 5.2 手動テスト実行

```bash
# 手動でタスクを実行してテスト
./run-manual.sh
```

### 5.3 ログ確認

```bash
# CloudWatch Logsでログを確認
aws logs tail /ecs/fx-analyzer-prod --follow
```

## 6. 投稿内容のカスタマイズ

### 6.1 WordPress記事フォーマット

`src/blog_publisher.py`の`format_analysis_for_blog`メソッドで記事のフォーマットをカスタマイズできます。

### 6.2 Twitter要約生成

`extract_summary_for_twitter`メソッドで、分析結果から自動的に要約を生成します。必要に応じてカスタマイズしてください。

## 7. トラブルシューティング

### WordPress投稿エラー

1. REST APIが有効か確認
2. アプリケーションパスワードが正しいか確認
3. パーマリンク設定を確認（「投稿名」推奨）

### Twitter API エラー

1. API権限が「Read and write」になっているか確認
2. アクセストークンを再生成してみる
3. レート制限に達していないか確認

### タイムゾーン問題

- ECSタスクはUTCで動作するため、EventBridgeルールは`cron(0 23 ? * MON-FRI *)`（UTC 23:00 = JST 8:00）
- コード内でJSTタイムゾーンを使用

## 8. セキュリティベストプラクティス

1. **APIキーの管理**
   - 本番環境では必ずAWS Secrets Managerを使用
   - .envファイルはGitにコミットしない

2. **権限の最小化**
   - WordPressユーザーは投稿権限のみ
   - Twitter APIは必要最小限の権限

3. **監視とアラート**
   - CloudWatch Alarmsで失敗を検知
   - SNSで通知を受け取る

## 9. 今後の拡張案

- 複数通貨ペアの分析投稿
- 投稿時間のカスタマイズ
- 分析精度に基づく自動投稿判断
- コメント返信機能の実装