# WordPress + X (Twitter) 連携ガイド

## 必要な情報と取得方法

### 1. WordPress側の必要情報

#### 1.1 サイト情報
```
WORDPRESS_URL=https://your-domain.com  # あなたのWordPressサイトURL
```

#### 1.2 認証情報（アプリケーションパスワード）
```
WORDPRESS_USERNAME=your_username         # WordPressユーザー名
WORDPRESS_PASSWORD=xxxx-xxxx-xxxx-xxxx  # アプリケーションパスワード
```

**アプリケーションパスワードの取得手順：**
1. WordPress管理画面にログイン
2. 「ユーザー」→「プロフィール」
3. 下部の「アプリケーションパスワード」セクション
4. 新しいアプリケーション名を入力（例：`FX-Analysis-Bot`）
5. 「新しいアプリケーションパスワードを追加」クリック
6. 表示されたパスワードをコピー（スペースは削除）

### 2. X (Twitter) API側の必要情報

#### 2.1 API認証情報
```
TWITTER_API_KEY=your_api_key                    # API Key (Consumer Key)
TWITTER_API_SECRET=your_api_secret              # API Key Secret
TWITTER_ACCESS_TOKEN=your_access_token          # Access Token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret   # Access Token Secret
```

**X Developer Portalでの取得手順：**

1. **開発者アカウント申請**
   - https://developer.twitter.com/ にアクセス
   - 「Sign up」から申請（承認に1-3日かかる場合あり）
   - 用途説明が必要（例：「Automated posting of educational FX analysis」）

2. **プロジェクトとアプリ作成**
   ```
   Developer Portal → Projects & Apps → Create Project
   - Project name: FX Analysis Bot
   - App name: fx-analysis-publisher
   - Use case: Publishing educational content
   ```

3. **API Keys取得**
   ```
   App settings → Keys and tokens
   - API Key & Secret → Generate
   - Access Token & Secret → Generate
   ```

4. **権限設定（重要）**
   ```
   App settings → User authentication settings
   - App permissions: Read and write ← 必須！
   - Type of App: Web App
   - Callback URI: https://your-domain.com/callback
   - Website URL: https://your-domain.com
   ```

### 3. 実際の連携設定

#### 3.1 .envファイルの設定
```bash
# WordPress設定
WORDPRESS_URL=https://your-blog.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=Wxyz 1234 5678 9ABC DEFG HIJK  # スペースは削除

# X (Twitter) API設定
TWITTER_API_KEY=1234567890abcdefghijk
TWITTER_API_SECRET=abcdefghijk1234567890lmnopqrstuvwxyz
TWITTER_ACCESS_TOKEN=1234567890-abcdefghijklmnopqrstuvwxyz
TWITTER_ACCESS_TOKEN_SECRET=abcdefghijklmnopqrstuvwxyz1234567890

# ブログ投稿設定
ENABLE_BLOG_POSTING=true
BLOG_POST_HOUR=8
```

#### 3.2 AWS Secrets Managerへの登録
```bash
# 現在のシークレットを取得
aws secretsmanager get-secret-value \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --query SecretString \
    --output text > secrets.json

# secrets.jsonを編集して上記の値を追加

# シークレットを更新
aws secretsmanager update-secret \
    --secret-id fx-analyzer-ecs-secrets-prod \
    --secret-string file://secrets.json

# ファイルを削除
rm secrets.json
```

### 4. 連携テスト

#### 4.1 ローカルテスト
```python
# test_integration.py
import os
from dotenv import load_dotenv
from src.blog_publisher import BlogPublisher

load_dotenv()

# 設定確認
print("WordPress URL:", os.getenv("WORDPRESS_URL"))
print("Twitter API Key:", os.getenv("TWITTER_API_KEY")[:10] + "...")

# テスト投稿
wordpress_config = {
    "url": os.getenv("WORDPRESS_URL"),
    "username": os.getenv("WORDPRESS_USERNAME"),
    "password": os.getenv("WORDPRESS_PASSWORD")
}

twitter_config = {
    "api_key": os.getenv("TWITTER_API_KEY"),
    "api_secret": os.getenv("TWITTER_API_SECRET"),
    "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
    "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
}

publisher = BlogPublisher(wordpress_config, twitter_config)

# テスト記事投稿
test_analysis = "テスト分析内容..."
test_charts = {}  # 実際はチャート画像パス

results = publisher.publish_analysis(test_analysis, test_charts)
print("WordPress URL:", results['wordpress_url'])
print("Twitter URL:", results['twitter_url'])
```

### 5. よくあるエラーと対処法

#### WordPress側
- **401 Unauthorized**: アプリケーションパスワードが間違っている
- **403 Forbidden**: REST APIが無効化されている → パーマリンク設定確認
- **404 Not Found**: URLが間違っている → 末尾スラッシュなし確認

#### X (Twitter)側
- **401 Unauthorized**: API認証情報が間違っている
- **403 Forbidden**: 権限不足 → Read and write権限を確認
- **429 Too Many Requests**: レート制限 → 15分待って再試行

### 6. セキュリティベストプラクティス

1. **APIキーの管理**
   - 本番環境では必ずAWS Secrets Manager使用
   - .envファイルは.gitignoreに追加
   - APIキーを定期的に再生成

2. **アクセス制限**
   - WordPressユーザーは投稿権限のみ付与
   - X APIは必要最小限の権限のみ

3. **監視**
   - CloudWatch Logsで投稿成功/失敗を監視
   - 異常な投稿パターンの検知

### 7. 動作確認チェックリスト

- [ ] WordPress REST APIアクセス確認
  ```bash
  curl https://your-domain.com/wp-json/wp/v2/posts
  ```

- [ ] X API認証確認
  ```bash
  curl -X GET "https://api.twitter.com/2/users/me" \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  ```

- [ ] ローカルテスト成功
- [ ] AWS Secrets Manager更新
- [ ] ECSタスク定義更新
- [ ] 手動実行でのテスト

### 8. トラブルシューティング

#### デバッグモード実行
```bash
# 詳細ログ出力
python -m src.main --debug

# 環境変数確認
python -c "import os; print(os.getenv('WORDPRESS_URL'))"
```

#### ログ確認
```bash
# ECSログ確認
aws logs tail /ecs/fx-analyzer-prod --follow --filter-pattern "blog"
```