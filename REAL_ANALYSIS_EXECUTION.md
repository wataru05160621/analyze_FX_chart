# 実分析の実行方法

## 作成したスクリプト

### 1. `execute_real_analysis.py`
- 完全な分析フロー
- すべての出力先に投稿
- 詳細なログ出力

### 2. `run_real_analysis.py`
- シンプルな実行
- エラーハンドリング付き
- 分析結果をファイル保存

### 3. `execute_production.py`
- 本番システム（main_multi_currency）を使用
- 8時モードで実行

## 実行手順

ターミナルで以下を実行してください：

```bash
# ディレクトリに移動
cd /Users/shinzato/programing/claude_code/analyze_FX_chart

# 実分析を実行（推奨）
python3 run_real_analysis.py

# または完全版
python3 execute_real_analysis.py

# または本番システム
python3 execute_production.py
```

## 実行内容

1. **チャート生成**
   - USD/JPYの5分足、1時間足
   - 288本のローソク足データ
   - PNGファイルとして保存

2. **Claude API分析**
   - フル機能版のClaudeAnalyzer使用
   - プライスアクションの原則に基づく詳細分析
   - 2000文字以上の分析レポート

3. **Slack通知**
   - Phase 1経由でアラート送信
   - 分析サマリーを含む

4. **Notion投稿**
   - 分析結果とチャート画像を含むページ作成
   - データベースに自動追加

5. **WordPress投稿**
   - チャート画像をアップロード
   - 分析記事を投稿（下書きまたは公開）
   - カテゴリ・タグ自動設定

6. **Twitter投稿**
   - 分析サマリーをツイート
   - ブログURLを含む

## 出力ファイル

- `screenshots/real_analysis/` - チャート画像
- `real_analysis_result.txt` - 分析結果のテキスト
- `latest_analysis.txt` - 最新の分析結果

## 確認方法

### Slack
設定したチャンネルで以下を確認：
- FX Analysis Alertメッセージ
- 分析サマリー

### Notion
データベースで以下を確認：
- 新規ページ（タイトル: USD/JPY実分析）
- チャート画像の表示
- 分析内容

### WordPress
https://by-price-action.com/wp-admin/ で以下を確認：
- 投稿一覧に新規記事
- チャート画像の埋め込み
- 分析内容の表示

### Twitter
アカウントのタイムラインで以下を確認：
- 新規ツイート
- ブログ記事へのリンク

## トラブルシューティング

### エラーが出る場合
1. `pip3 install -r requirements.txt` で依存関係をインストール
2. 各プラットフォームのAPI制限を確認
3. インターネット接続を確認

### 投稿が表示されない場合
1. 認証情報が正しいか確認
2. ログファイルを確認: `cat logs/fx_analysis.log`
3. 各プラットフォームの管理画面を確認

## 実行ログ

実行後、以下のログが出力されます：
- チャート生成の成功/失敗
- 分析文字数
- 各プラットフォームへの投稿結果
- エラー内容（ある場合）

正常に実行されれば、すべてのプラットフォームに実際の分析結果が画像付きで投稿されます。