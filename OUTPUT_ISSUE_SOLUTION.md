# FX分析システム 出力問題の解決策

## 問題の概要

1. **APIレート制限**: 40,000トークン/分の制限により複数通貨の同時分析でエラー
2. **出力先への投稿失敗**: ブログ、Slack、Xへの投稿が実行されていない

## 実施した改善

### 1. APIレート制限対策 ✅

`multi_currency_analyzer_optimized.py`を修正:
```python
# 各分析の間に60秒の遅延を追加
if analysis_results:  # 2つ目以降の分析の場合
    wait_time = 60  # 60秒待機
    logger.info(f"レート制限対策のため{wait_time}秒待機中...")
    await asyncio.sleep(wait_time)
```

**効果**:
- 3通貨分析で合計2分の追加時間
- レート制限エラーを確実に回避

### 2. 出力先への投稿問題の原因

#### Slack（Phase 1）
- **原因**: `ENABLE_PHASE1`が設定されていない可能性
- **解決策**: `.env.phase1`で`ENABLE_PHASE1=true`を確認

#### WordPress投稿
- **原因**: WordPress認証情報が未設定
- **解決策**: `.env`ファイルに以下を追加:
```bash
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_application_password
```

#### X (Twitter)
- **原因**: Twitter API認証情報が未設定
- **解決策**: `.env`ファイルに以下を追加:
```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

## テスト実行方法

### 1. 環境変数の確認
```bash
python check_env_settings.py
```

### 2. 完全なテスト実行
```bash
python test_all_outputs_fixed.py
```

このテストスクリプトは以下を実行:
1. 環境変数の確認
2. チャート生成
3. Claude分析（レート制限考慮）
4. Slack通知（Phase 1経由）
5. Notion投稿
6. WordPress投稿
7. X用コンテンツ生成

### 3. 本番実行（8時のブログ投稿モード）
```bash
FORCE_HOUR=8 python -m src.main_multi_currency
```

## 必要な設定

### 最低限必要な設定（Slack通知を有効にする）

1. `.env.phase1`を編集:
```bash
ENABLE_PHASE1=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

2. `.env`を確認:
```bash
CLAUDE_API_KEY=sk-ant-api03-...
NOTION_API_KEY=ntn_...
NOTION_DATABASE_ID=...
```

### WordPress投稿を有効にする

`.env`に追加:
```bash
# WordPress設定
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_app_password

# ブログ投稿を有効化
ENABLE_BLOG_POSTING=true
```

### X (Twitter)投稿を有効にする

`.env`に追加:
```bash
# Twitter API設定
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
```

## 動作確認チェックリスト

- [ ] Claude API分析が成功する（レート制限なし）
- [ ] Slackに通知が届く
- [ ] Notionにページが作成される
- [ ] WordPressに記事が投稿される（設定済みの場合）
- [ ] X用のコンテンツが生成される

## トラブルシューティング

### Slack通知が届かない
1. Webhook URLが正しいか確認
2. `ENABLE_PHASE1=true`になっているか確認
3. `logs/phase1_*.log`でエラーを確認

### WordPress投稿が失敗する
1. アプリケーションパスワードを使用しているか確認
2. XML-RPC APIが有効になっているか確認
3. `logs/fx_analysis.log`でエラーを確認

### レート制限エラーが続く
1. 待機時間を90秒または120秒に増やす
2. 分析する通貨ペアを減らす
3. APIプランのアップグレードを検討