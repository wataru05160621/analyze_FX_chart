# Claude API オーバーロード対策

## 現在の状況
- Claude APIがError 529 (Overloaded)を返している
- 一時的にAPIが利用できない状態

## 対処法

### 1. リトライ機能付き実行（推奨）
```bash
python3 execute_with_retry.py
```
- 30秒、60秒、120秒の間隔でリトライ
- 失敗時はデモ分析を使用

### 2. チャート画像のみ投稿
```bash
python3 execute_without_api.py
```
- Claude分析をスキップ
- チャート画像付きでWordPressに投稿
- 簡易的な説明文を追加

### 3. 時間をおいて再実行
```bash
# 30分後に再実行
sleep 1800 && python3 run_real_analysis.py

# または1時間後
sleep 3600 && python3 execute_production.py
```

## 実行したスクリプト

### `execute_with_retry.py`
- APIエラー時に自動リトライ
- 最大3回まで試行
- 失敗時はデモ分析で投稿継続

### `execute_without_api.py`
- チャート画像生成のみ
- WordPress、Slackに投稿
- API分析なしで動作

## 確認事項

1. **チャート画像は正常に生成されている**
   - screenshots/ディレクトリに保存
   - 5分足、1時間足の2枚

2. **投稿機能は正常**
   - WordPress投稿可能
   - Slack通知可能
   - Notion投稿可能

3. **Claude APIの状態**
   - 一時的なオーバーロード
   - 通常は数分〜数時間で回復

## 推奨アクション

1. まず`execute_without_api.py`でチャート画像を投稿
2. 30分後に`execute_with_retry.py`で詳細分析を試行
3. それでも失敗する場合は、翌日の定期実行を待つ

## 代替API

将来的な対策として：
- OpenAI GPT-4 Vision
- Google Gemini Vision
- 複数APIのフォールバック機能

## ログ確認
```bash
# 最新のエラーログ
tail -n 50 logs/fx_analysis.log

# Claude関連のエラー
grep -i "claude\|529\|overload" logs/*.log
```