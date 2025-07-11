import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import requests

# 環境変数
PERFORMANCE_TABLE = os.environ.get('PERFORMANCE_TABLE', 'phase1-performance')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK_URL')
PRICE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
S3_BUCKET = os.environ.get('PERFORMANCE_S3_BUCKET', 'fx-analysis-performance')

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """24時間後のシグナル検証"""
    print(f"Event received: {json.dumps(event)}")
    
    try:
        # EventBridgeまたは直接呼び出しからシグナルID取得
        if 'detail' in event:
            signal_id = event['detail']['signal_id']
            currency_pair = event['detail'].get('currency_pair', 'USDJPY')
        else:
            signal_id = event.get('signal_id')
            currency_pair = event.get('currency_pair', 'USDJPY')
        
        # S3からパフォーマンスデータを取得
        performance_data = get_performance_data()
        
        # シグナルを検索
        signal = find_signal(performance_data, signal_id)
        if not signal:
            raise Exception(f"Signal not found: {signal_id}")
        
        # 現在価格を取得
        current_price = get_current_price(currency_pair)
        
        # 結果を判定
        result = verify_signal_result(signal, current_price)
        
        # データを更新
        update_signal_in_data(performance_data, signal_id, result)
        
        # 統計を再計算
        recalculate_statistics(performance_data)
        
        # S3に保存
        save_performance_data(performance_data)
        
        # Slack通知
        if SLACK_WEBHOOK:
            send_slack_notification(signal, result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Signal verified successfully',
                'signal_id': signal_id,
                'result': result
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_performance_data():
    """S3からパフォーマンスデータを取得"""
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key='phase1_performance.json')
        return json.loads(response['Body'].read())
    except s3.exceptions.NoSuchKey:
        # ファイルが存在しない場合は新規作成
        return {"signals": [], "statistics": {}, "last_updated": None}

def save_performance_data(data):
    """S3にパフォーマンスデータを保存"""
    data['last_updated'] = datetime.now().isoformat()
    s3.put_object(
        Bucket=S3_BUCKET,
        Key='phase1_performance.json',
        Body=json.dumps(data, indent=2),
        ContentType='application/json'
    )

def find_signal(data, signal_id):
    """シグナルを検索"""
    for signal in data.get('signals', []):
        if signal['id'] == signal_id:
            return signal
    return None

def update_signal_in_data(data, signal_id, result):
    """シグナルデータを更新"""
    for signal in data.get('signals', []):
        if signal['id'] == signal_id:
            signal['status'] = 'completed' if result['result'] != 'OPEN' else 'active'
            signal['result'] = result['result']
            signal['actual_exit'] = result['exit_price']
            signal['pnl'] = result['pnl']
            signal['pnl_percentage'] = result['pnl_percentage']
            signal['verified_at'] = result['verified_at']
            break

def get_current_price(currency_pair):
    """現在価格を取得（デモ実装）"""
    # 実際の実装ではAlpha Vantage APIなどを使用
    # ここではデモ価格を返す
    demo_prices = {
        'USDJPY': 145.75,
        'EURUSD': 1.0850,
        'GBPUSD': 1.2750
    }
    return demo_prices.get(currency_pair, 145.50)

def verify_signal_result(signal, current_price):
    """シグナルの結果を判定"""
    entry_price = float(signal['entry_price'])
    stop_loss = float(signal['stop_loss'])
    take_profit = float(signal['take_profit'])
    action = signal['action']
    
    if action == 'BUY':
        if current_price >= take_profit:
            result = 'TP_HIT'
            exit_price = take_profit
        elif current_price <= stop_loss:
            result = 'SL_HIT'
            exit_price = stop_loss
        else:
            result = 'OPEN'
            exit_price = current_price
        pnl = exit_price - entry_price
    else:  # SELL
        if current_price <= take_profit:
            result = 'TP_HIT'
            exit_price = take_profit
        elif current_price >= stop_loss:
            result = 'SL_HIT'
            exit_price = stop_loss
        else:
            result = 'OPEN'
            exit_price = current_price
        pnl = entry_price - exit_price
    
    pnl_percentage = (pnl / entry_price) * 100
    
    return {
        'result': result,
        'exit_price': exit_price,
        'pnl': pnl,
        'pnl_percentage': pnl_percentage,
        'verified_at': datetime.now().isoformat()
    }

def recalculate_statistics(data):
    """統計を再計算"""
    completed_signals = [s for s in data.get('signals', []) if s.get('status') == 'completed']
    
    if not completed_signals:
        return
    
    wins = [s for s in completed_signals if s.get('pnl', 0) > 0]
    losses = [s for s in completed_signals if s.get('pnl', 0) <= 0]
    
    win_rate = len(wins) / len(completed_signals) if completed_signals else 0
    avg_win = sum(s.get('pnl', 0) for s in wins) / len(wins) if wins else 0
    avg_loss = sum(abs(s.get('pnl', 0)) for s in losses) / len(losses) if losses else 0
    
    expected_value = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    data['statistics'] = {
        'total_trades': len(completed_signals),
        'win_rate': win_rate,
        'expected_value': expected_value,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'updated_at': datetime.now().isoformat()
    }

def send_slack_notification(signal, result):
    """Slack通知を送信"""
    emoji = "✅" if result['pnl'] > 0 else "❌" if result['pnl'] < 0 else "⏳"
    
    message = f"""
{emoji} Phase 1 シグナル検証結果

シグナルID: {signal['id']}
通貨ペア: {signal.get('currency_pair', 'USD/JPY')}
アクション: {signal['action']}
結果: {result['result']}

エントリー: {signal['entry_price']}
エグジット: {result['exit_price']}
損益: {result['pnl']:.1f} pips ({result['pnl_percentage']:.2f}%)

検証時刻: {result['verified_at']}
"""
    
    requests.post(SLACK_WEBHOOK, json={"text": message})
