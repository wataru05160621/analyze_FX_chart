"""
TradingView価格アラート連携
分析結果の価格レベルでアラートを受信
"""
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from .phase1_alert_system import TradingViewAlertSystem

app = Flask(__name__)
alert_system = TradingViewAlertSystem()

# Phase 1で設定した価格レベルを保存
ACTIVE_ALERTS = {}


def register_price_levels(signal, currency_pair):
    """Phase 1のシグナルから価格レベルを登録"""
    
    alert_id = f"{currency_pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    ACTIVE_ALERTS[alert_id] = {
        'currency_pair': currency_pair,
        'signal': signal,
        'created_at': datetime.now().isoformat(),
        'triggered': False
    }
    
    return alert_id


@app.route('/tv-price-alert', methods=['POST'])
def handle_price_alert():
    """TradingViewからの価格アラートを処理"""
    
    data = request.json
    
    # TradingViewからのデータ
    # 例: {"symbol": "USDJPY", "price": 145.50}
    symbol = data.get('symbol')
    current_price = float(data.get('price'))
    
    # 登録されたアラートをチェック
    for alert_id, alert_info in ACTIVE_ALERTS.items():
        if alert_info['triggered']:
            continue
            
        signal = alert_info['signal']
        
        # エントリー価格に到達したかチェック
        if signal['action'] == 'BUY' and current_price >= signal['entry_price']:
            # 買いシグナル発動
            trigger_alert(alert_id, current_price)
            
        elif signal['action'] == 'SELL' and current_price <= signal['entry_price']:
            # 売りシグナル発動
            trigger_alert(alert_id, current_price)
    
    return jsonify({"status": "ok"})


def trigger_alert(alert_id, current_price):
    """アラートを発動"""
    
    alert_info = ACTIVE_ALERTS[alert_id]
    signal = alert_info['signal']
    
    # Slackに通知
    enhanced_signal = signal.copy()
    enhanced_signal['actual_entry'] = current_price
    
    alert_system.send_trade_alert({
        'signal': enhanced_signal,
        'summary': f"価格アラート発動！ {alert_info['currency_pair']} @ {current_price}"
    })
    
    # アラートを発動済みにマーク
    ACTIVE_ALERTS[alert_id]['triggered'] = True
    ACTIVE_ALERTS[alert_id]['triggered_at'] = datetime.now().isoformat()
    ACTIVE_ALERTS[alert_id]['triggered_price'] = current_price
    
    print(f"アラート発動: {alert_id} - {signal['action']} @ {current_price}")


# 統合スクリプト
def integrate_with_phase1():
    """Phase 1と統合"""
    
    from src.phase1_integration import Phase1FXAnalysisWithAlerts
    
    async def analyze_and_setup_alerts():
        # Phase 1で分析実行
        system = Phase1FXAnalysisWithAlerts()
        result = await system.analyze_and_alert()
        
        if result and result.get('signal'):
            signal = result['signal']
            
            if signal['action'] != 'NONE':
                # 価格レベルを登録
                alert_id = register_price_levels(signal, "USD/JPY")
                
                print(f"価格アラート登録: {alert_id}")
                print(f"- アクション: {signal['action']}")
                print(f"- エントリー: {signal['entry_price']}")
                print(f"- 損切り: {signal['stop_loss']}")
                print(f"- 利確: {signal['take_profit']}")
                
                # TradingViewで手動設定する価格レベルを表示
                print("\nTradingViewで以下の価格アラートを設定してください:")
                print(f"1. {signal['action']}シグナル: {signal['entry_price']}")
                print(f"2. 損切りアラート: {signal['stop_loss']}")
                print(f"3. 利確アラート: {signal['take_profit']}")


# 実際のTradingView設定方法
def print_tradingview_setup():
    """TradingView設定手順を表示"""
    
    print("""
=== TradingViewアラート設定手順 ===

1. TradingViewでUSD/JPYチャートを開く
2. アラートアイコンをクリック
3. 以下の設定を行う:

【買いシグナルの場合】
- 条件: USD/JPY が 以上 [エントリー価格]
- アラートアクション: 
  ✓ アプリに通知を表示
  ✓ Webhook URL: {webhook_url}
- メッセージ: {{"symbol": "USDJPY", "price": {{close}}}}

【売りシグナルの場合】
- 条件: USD/JPY が 以下 [エントリー価格]

4. 「作成」をクリック
""".format(webhook_url=os.environ.get('TRADINGVIEW_WEBHOOK_URL', 'http://your-server.com/tv-price-alert')))


if __name__ == '__main__':
    # Webhookサーバー起動
    print("TradingView Webhookサーバーを起動します...")
    print(f"Webhook URL: http://localhost:5000/tv-price-alert")
    print("\nngrokを使用して公開URLを生成してください:")
    print("ngrok http 5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)