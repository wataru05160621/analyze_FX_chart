# FX分析システム 実行手順

## 実行可能なスクリプト

### 1. 個別テスト

#### Slack通知テスト
```bash
python post_slack.py
```

#### WordPress投稿テスト
```bash
python post_wp.py
```

#### 完全な分析と投稿
```bash
python run_analysis_and_post.py
```

### 2. 本番実行

#### 8時モード（ブログ投稿あり）
```bash
FORCE_HOUR=8 python -m src.main_multi_currency
```

#### 通常実行
```bash
python -m src.main_multi_currency
```

## 現在の設定状態

### ✅ 有効な機能
- **Claude API**: 分析機能
- **Notion**: 自動投稿
- **Slack**: Phase 1通知
- **WordPress**: 設定済み（by-price-action.com）
- **Twitter**: API認証情報設定済み

### 環境変数の確認
```python
# .envファイルの主要設定
WORDPRESS_URL=https://by-price-action.com
WORDPRESS_USERNAME=publish
WORDPRESS_PASSWORD=aFIxNNhft0lSjkzwI75rYZk2
ENABLE_BLOG_POSTING=true

TWITTER_API_KEY=9lTKMamtQOrgxRn5Q87hcbJ07
TWITTER_API_SECRET=dRIUSBtg31YCf9u112Iy9pC6uHY75SFv67MoEx75nf0M0lz2Xm
TWITTER_ACCESS_TOKEN=1939874444509691904-B5JJStts2wtuOHAJD4vebzEq6RTXRb
TWITTER_ACCESS_TOKEN_SECRET=Et0qR6WOHkKPPffcDA6aCZIzhqIZyi1xs5pJBoWahW1Tq

# .env.phase1の主要設定
ENABLE_PHASE1=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
```

## 実行時の注意事項

1. **シェル環境エラー**
   - zprofileのエラーは無視して問題ありません
   - Pythonスクリプトは正常に動作します

2. **APIレート制限**
   - 複数通貨分析時は60秒の待機時間があります
   - 単一通貨（USD/JPY）のみの場合は制限なし

3. **投稿確認**
   - WordPress: 管理画面で下書きまたは公開済み記事を確認
   - Slack: 設定したチャンネルで通知を確認
   - Notion: データベースページで新規エントリを確認
   - Twitter: タイムラインで投稿を確認

## トラブルシューティング

### スクリプトが実行できない場合
```bash
# 実行権限を付与
chmod +x post_slack.py
chmod +x post_wp.py
chmod +x run_analysis_and_post.py

# Pythonパスを明示的に指定
/usr/bin/python3 スクリプト名.py
```

### 投稿が失敗する場合
1. インターネット接続を確認
2. 認証情報が正しいか確認
3. APIの利用制限を確認
4. ログファイルを確認: `logs/fx_analysis.log`

## 推奨実行方法

開発/テスト環境:
```bash
python run_analysis_and_post.py
```

本番環境（ECS/cron）:
```bash
python -m src.main_multi_currency
```

## 次のステップ

1. 各スクリプトを手動で実行
2. 各プラットフォームで投稿を確認
3. 問題があれば個別にデバッグ
4. 定期実行の設定（cron/ECS）