# スケジューラーセットアップガイド

FX分析を日本時間の8:00、15:00、21:00に自動実行する方法を説明します。

## 実行方法の選択

### 方法1: ローカルマシンでの実行

#### A. Pythonスケジューラー（推奨）

```bash
# スケジューラーを起動
python run_scheduler.py

# バックグラウンドで実行
nohup python run_scheduler.py > logs/scheduler.log 2>&1 &
```

#### B. Cronジョブ

```bash
# cronジョブを設定
chmod +x scripts/setup_cron.sh
./scripts/setup_cron.sh

# 手動でcronを編集する場合
crontab -e

# 以下を追加
0 8 * * * cd /path/to/project && python3 run_scheduler.py --once >> logs/cron.log 2>&1
0 15 * * * cd /path/to/project && python3 run_scheduler.py --once >> logs/cron.log 2>&1
0 21 * * * cd /path/to/project && python3 run_scheduler.py --once >> logs/cron.log 2>&1
```

#### C. systemdサービス（Linux）

1. サービスファイルを作成:

```bash
sudo nano /etc/systemd/system/fx-analyzer.service
```

2. 以下の内容を記述:

```ini
[Unit]
Description=FX Chart Analyzer Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/analyze_FX_chart
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /path/to/analyze_FX_chart/scripts/run_as_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. サービスを有効化:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fx-analyzer
sudo systemctl start fx-analyzer

# ステータス確認
sudo systemctl status fx-analyzer

# ログ確認
sudo journalctl -u fx-analyzer -f
```

### 方法2: GitHub Actions（推奨）

GitHub Actionsを使用すると、サーバー不要で自動実行できます。

1. リポジトリの Settings → Secrets and variables → Actions で以下のシークレットを設定:

   - `OPENAI_API_KEY`
   - `NOTION_API_KEY`
   - `NOTION_DATABASE_ID`
   - `TRADINGVIEW_CUSTOM_URL`
   - `CHATGPT_EMAIL`
   - `CHATGPT_PASSWORD`
   - `CHATGPT_PROJECT_NAME`
   - `USE_WEB_CHATGPT`
   - `IMGUR_CLIENT_ID`（画像アップロード用）

2. `.github/workflows/fx_analysis.yml`は既に設定済み

3. 手動実行テスト:
   - Actions タブ → FX Chart Analysis → Run workflow

### 方法3: クラウドサービス

#### AWS Lambda + EventBridge

1. Dockerイメージを作成:

```dockerfile
FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps

COPY . .

CMD ["lambda_handler.handler"]
```

2. EventBridgeでスケジュールルールを作成（JST時刻で設定）

#### Google Cloud Functions + Cloud Scheduler

同様にCloud Functionsとして実装し、Cloud Schedulerで定時実行

## テスト実行

### 1回だけ実行（動作確認）

```bash
# 1回だけ実行
python run_scheduler.py --once

# または直接実行
python -m src.main
```

### スケジューラーの動作確認

```bash
# スケジューラーを起動（実際の時刻まで待機）
python run_scheduler.py

# ログを確認
tail -f logs/scheduler.log
```

## トラブルシューティング

### タイムゾーンの問題

```bash
# システムのタイムゾーンを確認
date
timedatectl

# 必要に応じてタイムゾーンを設定
sudo timedatectl set-timezone Asia/Tokyo
```

### 権限の問題

```bash
# スクリプトに実行権限を付与
chmod +x scripts/*.sh
chmod +x scripts/*.py

# ログディレクトリの権限
chmod 755 logs/
```

### プロセスの確認

```bash
# 実行中のプロセスを確認
ps aux | grep -E "python.*scheduler|fx.*analyze"

# プロセスを停止
kill -TERM <PID>
```

## ログの確認

```bash
# スケジューラーログ
tail -f logs/scheduler.log

# 分析実行ログ
tail -f logs/fx_analysis.log

# cronログ（cronを使用している場合）
tail -f logs/cron.log

# systemdログ（systemdを使用している場合）
sudo journalctl -u fx-analyzer -f
```

## 注意事項

1. **リソース使用量**: Playwrightは比較的重いため、適切なマシンリソースを確保
2. **API制限**: ChatGPT APIやNotion APIの利用制限に注意
3. **セキュリティ**: 認証情報は環境変数で管理し、コードに直接記載しない
4. **エラー通知**: 重要なエラーは通知するように設定することを推奨