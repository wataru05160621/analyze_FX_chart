# TradingViewアラート設定ガイド

## 概要
TradingViewのアラートをPhase 1システムと連携させる方法

## 方法1: Webhook経由（推奨）

### 1. TradingViewでアラート作成
1. チャートを開く
2. アラートアイコンをクリック
3. 条件を設定（例：RSI > 70）
4. 「Webhook URL」にチェック
5. URLを入力: `https://your-domain.com/tradingview-webhook`

### 2. Webhookサーバー構築

```python
# webhook_server.py
from flask import Flask, request
import json
from src.phase1_alert_system import TradingViewAlertSystem

app = Flask(__name__)
alert_system = TradingViewAlertSystem()

@app.route('/tradingview-webhook', methods=['POST'])
def handle_tradingview_alert():
    """TradingViewからのアラートを受信"""
    data = request.json
    
    # TradingViewのアラートメッセージをパース
    # 例: "BUY USDJPY @ 145.50 SL:145.20 TP:146.00"
    message = data.get('message', '')
    
    # シグナルを生成
    signal = parse_tradingview_message(message)
    
    # Slackに転送
    alert_system.send_trade_alert({
        'signal': signal,
        'summary': f"TradingView Alert: {message}"
    })
    
    return "OK", 200

def parse_tradingview_message(message):
    """TradingViewメッセージをパース"""
    parts = message.split()
    return {
        'action': parts[0],  # BUY/SELL
        'entry_price': float(parts[3]),
        'stop_loss': float(parts[4].split(':')[1]),
        'take_profit': float(parts[5].split(':')[1]),
        'confidence': 0.9  # TradingViewアラートは高信頼度
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### 3. ngrokでローカルテスト

```bash
# ngrokインストール
brew install ngrok

# ローカルサーバーを公開
ngrok http 8080

# 生成されたURLをTradingViewに設定
# 例: https://abc123.ngrok.io/tradingview-webhook
```

## 方法2: メール経由

### 1. TradingViewアラートをメール送信
- アラート設定で「メール送信」を有効化
- 専用メールアドレスを用意

### 2. メール監視スクリプト

```python
# email_monitor.py
import imaplib
import email
from src.phase1_alert_system import SignalGenerator, TradingViewAlertSystem

def monitor_tradingview_emails():
    """TradingViewからのメールを監視"""
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('your-email@gmail.com', 'app-password')
    mail.select('inbox')
    
    # 未読メールを検索
    _, data = mail.search(None, 'UNSEEN', 'FROM', 'noreply@tradingview.com')
    
    for num in data[0].split():
        _, data = mail.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        
        # メール本文からシグナルを抽出
        body = get_email_body(msg)
        signal = parse_email_content(body)
        
        # Slackに送信
        alert_system.send_trade_alert({
            'signal': signal,
            'summary': f"TradingView: {body[:200]}"
        })
```

## 方法3: Chrome拡張機能

TradingViewのアラートをリアルタイムでキャプチャする拡張機能を作成

```javascript
// content.js
// TradingViewのアラートポップアップを監視
const observer = new MutationObserver((mutations) => {
    const alerts = document.querySelectorAll('.tv-alert-notification');
    alerts.forEach(alert => {
        const message = alert.textContent;
        // WebhookでPythonサーバーに送信
        fetch('http://localhost:8080/tradingview-alert', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: message})
        });
    });
});

observer.observe(document.body, {childList: true, subtree: true});
```

## 推奨設定

### TradingViewアラートメッセージフォーマット
```
{{strategy.order.action}} {{ticker}} @ {{close}} SL:{{plot("SL")}} TP:{{plot("TP")}}
```

### 例
```
BUY USDJPY @ 145.50 SL:145.20 TP:146.00
SELL EURUSD @ 1.0850 SL:1.0880 TP:1.0800
```

## セキュリティ考慮事項

1. **Webhook認証**
   ```python
   # シークレットトークンで認証
   SECRET_TOKEN = os.environ.get('TRADINGVIEW_SECRET')
   
   if request.headers.get('X-Auth-Token') != SECRET_TOKEN:
       return "Unauthorized", 401
   ```

2. **SSL/TLS必須**
   - HTTPSでのみWebhookを受信
   - Let's Encryptで無料SSL証明書取得

3. **レート制限**
   - 1分間に10リクエストまで
   - DDoS対策

## 実装優先順位

1. **Phase 1完成後すぐ**: Webhook経由（ngrokでテスト）
2. **本番環境**: AWS API Gateway + Lambda
3. **高度な統合**: カスタムインジケーターとの連携