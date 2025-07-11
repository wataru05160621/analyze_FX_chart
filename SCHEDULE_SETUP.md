# スケジュール実行設定ガイド

## 実行スケジュール
- **平日8時**: ブログ、X（Twitter）、Notion投稿
- **平日15時**: Notion投稿のみ（ロンドンセッション）
- **平日21時**: Notion投稿のみ（NYセッション）

## 設定方法

### 方法1: Pythonスケジューラー（推奨）

```bash
# バックグラウンドで常時実行
nohup python3 scheduled_execution.py > logs/scheduler.log 2>&1 &

# または、ターミナルで直接実行
python3 scheduled_execution.py
```

### 方法2: cron設定

1. cron設定スクリプトを実行:
```bash
./cron_setup.sh
```

2. crontabを編集:
```bash
crontab -e
```

3. 以下を追加:
```cron
# FX分析システム スケジュール実行
# 平日8時: ブログ、X、Notion投稿
0 8 * * 1-5 cd /Users/shinzato/programing/claude_code/analyze_FX_chart && ./run_scheduled_analysis.sh

# 平日15時: Notion投稿のみ
0 15 * * 1-5 cd /Users/shinzato/programing/claude_code/analyze_FX_chart && ./run_scheduled_analysis.sh

# 平日21時: Notion投稿のみ
0 21 * * 1-5 cd /Users/shinzato/programing/claude_code/analyze_FX_chart && ./run_scheduled_analysis.sh
```

### 方法3: launchd（macOS推奨）

`com.fx.analysis.plist`を作成して`~/Library/LaunchAgents/`に配置

## テスト実行

### フル投稿テスト（8時相当）
```bash
python3 scheduled_execution.py --test full
```

### Notionのみテスト（15時/21時相当）
```bash
python3 scheduled_execution.py --test notion
```

### 個別実行
```bash
# 8時相当（全プラットフォーム）
python3 execute_complete_posting.py

# 15時/21時相当（Notionのみ）
python3 execute_notion_only.py --session "ロンドンセッション"
python3 execute_notion_only.py --session "NYセッション"
```

## ログ確認

```bash
# スケジューラーログ
tail -f logs/scheduler.log

# cron実行ログ
tail -f logs/cron/analysis_$(date +%Y%m%d).log

# 分析ログ
tail -f logs/fx_analysis.log
```

## プロセス管理

### スケジューラーの確認
```bash
ps aux | grep scheduled_execution.py
```

### スケジューラーの停止
```bash
# プロセスIDを確認して
kill [PID]
```

### スケジューラーの再起動
```bash
# 停止後に再度起動
nohup python3 scheduled_execution.py > logs/scheduler.log 2>&1 &
```

## トラブルシューティング

### スケジュールが実行されない
1. タイムゾーン確認: `date`コマンドで現在時刻確認
2. 権限確認: スクリプトに実行権限があるか
3. 環境変数: `.env`ファイルが正しく読み込まれているか

### エラー通知
- Slackに自動通知されます
- ログファイルで詳細確認

### メモリ不足
- 古いログファイルを定期的に削除
- スクリーンショットディレクトリをクリーンアップ

## 運用上の注意

1. **週末は自動スキップ**
   - 土日は実行されません
   - 祝日は手動で停止が必要

2. **API制限**
   - Claude API: レート制限に注意
   - 各プラットフォームのAPI制限確認

3. **ディスク容量**
   - screenshots/ディレクトリが肥大化しないよう定期削除
   - ログファイルのローテーション設定

4. **バックアップ**
   - 分析結果は自動保存
   - 重要な分析はNotionでアーカイブ