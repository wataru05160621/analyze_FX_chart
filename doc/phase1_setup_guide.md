# Phase 1: アラートシステム セットアップガイド

## 概要
Phase 1では、FX分析結果から売買シグナルを生成し、Slack、メール、TradingViewに通知するシステムを実装します。

## セットアップ手順

### 1. Slack Webhook設定

#### Step 1: Slack Appを作成
1. [Slack API](https://api.slack.com/apps) にアクセス
2. "Create New App" → "From scratch" を選択
3. App名を入力（例：FX Trading Alerts）
4. ワークスペースを選択

#### Step 2: Incoming Webhookを有効化
1. 左メニューから "Incoming Webhooks" を選択
2. "Activate Incoming Webhooks" をONに
3. "Add New Webhook to Workspace" をクリック
4. 通知を送信するチャンネルを選択
5. 生成されたWebhook URLをコピー

#### Step 3: 環境変数に設定
```bash
# .env.phase1 ファイルを作成
cp .env.phase1.example .env.phase1

# Webhook URLを設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 2. メール通知設定（Gmail例）

#### Step 1: Gmailアプリパスワードを生成
1. [Googleアカウント設定](https://myaccount.google.com/security) にアクセス
2. 2段階認証を有効化
3. "アプリパスワード" を選択
4. アプリ：メール、デバイス：その他（カスタム名）を選択
5. 生成された16文字のパスワードをコピー

#### Step 2: 環境変数に設定
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-char-app-password
RECIPIENT_EMAIL=recipient@example.com
```

### 3. 必要なパッケージのインストール

```bash
# 既存のrequirements.txtに追加
echo "python-dotenv==1.0.0" >> requirements.txt
echo "boto3==1.26.137" >> requirements.txt

# インストール
pip install -r requirements.txt
```

### 4. テスト実行

#### 単体テストの実行
```bash
# テストコードを実行
python -m pytest tests/test_phase1_alert_system.py -v
```

#### 統合テストの実行（テストモード）
```bash
# テストモードで強制実行
TEST_MODE=1 python src/phase1_integration.py
```

### 5. 本番環境での設定

#### AWS DynamoDBテーブル作成（オプション）
```bash
# AWS CLIでテーブル作成
aws dynamodb create-table \
    --table-name fx-trading-signals \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-northeast-1
```

#### Cronジョブ設定
```bash
# crontabを編集
crontab -e

# 8:00, 15:00, 21:00に実行
0 8,15,21 * * * cd /path/to/analyze_FX_chart && /usr/bin/python3 src/phase1_integration.py >> logs/phase1.log 2>&1
```

## 動作確認

### 1. Slack通知テスト
```python
# テスト用スクリプト
from src.phase1_alert_system import TradingViewAlertSystem

alert_system = TradingViewAlertSystem()
test_alert = {
    'symbol': 'USD/JPY',
    'action': 'BUY',
    'entry': 145.50,
    'stop_loss': 145.20,
    'take_profit': 146.00,
    'confidence': 0.85,
    'analysis': 'テスト通知です'
}

alert_system._send_slack_notification(test_alert)
```

### 2. シグナル生成テスト
```python
from src.phase1_alert_system import SignalGenerator

generator = SignalGenerator()
test_text = """
USD/JPYは145.50で強いブレイクアウトを確認。
146.00を目標に、145.20を損切りとして買いエントリー推奨。
"""

signal = generator.generate_trading_signal(test_text)
print(signal)
```

## トラブルシューティング

### Slack通知が届かない
1. Webhook URLが正しいか確認
2. Slackワークスペースの権限を確認
3. ファイアウォール設定を確認

### メール通知が届かない
1. Gmailの場合、アプリパスワードを使用しているか確認
2. 迷惑メールフォルダを確認
3. SMTP設定が正しいか確認

### シグナルが生成されない
1. 分析テキストにキーワードが含まれているか確認
2. 価格パターンが正しい形式か確認
3. ログファイルでエラーを確認

## 次のステップ（Phase 2準備）

1. OANDA デモ口座の開設
2. OANDA API トークンの取得
3. AWS Lambda環境の準備

詳細は `auto_trading_implementation_plan.md` のPhase 2セクションを参照してください。