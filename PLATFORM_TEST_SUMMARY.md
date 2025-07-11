# プラットフォーム投稿テスト実行サマリー

## 実行日時
2025-07-11

## テスト用スクリプト

### 1. WordPress直接投稿テスト
```bash
python direct_wordpress_test.py
```
- **URL**: https://by-price-action.com
- **ユーザー**: publish
- **投稿方法**: WordPress REST API
- **投稿ステータス**: draft（下書き）

### 2. Twitter直接投稿テスト
```bash
python direct_twitter_test.py
```
- **API**: v1.1およびv2
- **認証**: OAuth 1.0a
- **投稿内容**: テストツイート

### 3. 完全な投稿テスト（全プラットフォーム）
```bash
python post_to_all_platforms.py
```
- チャート生成
- Claude分析
- Slack通知
- Notion投稿
- WordPress投稿
- Twitter投稿

### 4. 本番実行（8時モード）
```bash
FORCE_HOUR=8 python -m src.main_multi_currency
```
または
```bash
python execute_blog_post.py
```

## 確認方法

### WordPress
1. 管理画面にログイン: https://by-price-action.com/wp-admin/
2. 投稿一覧を確認
3. 下書きまたは公開済み記事を確認

### Twitter/X
1. 設定したアカウントのタイムラインを確認
2. ツイートが投稿されているか確認

### Slack
1. 設定したチャンネルを確認
2. Phase 1アラートが通知されているか確認

### Notion
1. データベースページを確認
2. 新規ページが作成されているか確認

## トラブルシューティング

### WordPress投稿が失敗する場合
- XML-RPC APIが有効か確認
- アプリケーションパスワードが正しいか確認
- REST APIエンドポイントにアクセスできるか確認

### Twitter投稿が失敗する場合
- API制限に達していないか確認
- アプリの権限設定を確認（Read and Write必要）
- アクセストークンが有効か確認

### 実行環境の問題
- Pythonパスの問題がある場合は、直接スクリプトを実行
- 環境変数が読み込まれない場合は、スクリプト内で直接設定

## 実行ログの確認
```bash
# 最新のログを確認
tail -n 50 logs/fx_analysis.log

# エラーログを確認
tail -n 50 logs/src.main_multi_currency_errors.log
```