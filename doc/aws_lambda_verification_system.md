# AWS Lambda 自動検証システム

## 概要
Phase 1のシグナルを24時間後に自動検証するAWS Lambdaベースのシステムです。

## アーキテクチャ

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Phase 1   │────▶│  EventBridge │────▶│   Lambda    │
│   Signal    │     │  (24h delay) │     │  Function   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                            ┌──────────────────────────────┐
                            │        S3 / DynamoDB         │
                            │    Performance Storage       │
                            └──────────────────────────────┘
```

## 実装詳細

### 1. Lambda関数

```python
# lambda/verify_signal/handler.py
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import requests

# 環境変数
PERFORMANCE_TABLE = os.environ['PERFORMANCE_TABLE']
SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK_URL']
PRICE_API_KEY = os.environ['PRICE_API_KEY']

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(PERFORMANCE_TABLE)

def lambda_handler(event, context):
    """
    24時間後のシグナル検証
    EventBridgeから呼び出される
    """
    print(f"Event received: {json.dumps(event)}")
    
    try:
        # EventBridgeのペイロードからシグナルID取得
        signal_id = event['detail']['signal_id']
        currency_pair = event['detail']['currency_pair']
        
        # DynamoDBからシグナル情報取得
        response = table.get_item(Key={'signal_id': signal_id})
        
        if 'Item' not in response:
            raise Exception(f"Signal not found: {signal_id}")
        
        signal = response['Item']
        
        # 現在価格を取得
        current_price = get_current_price(currency_pair)
        
        # 結果を判定
        result = verify_signal_result(signal, current_price)
        
        # DynamoDBを更新
        update_signal_result(signal_id, result)
        
        # Slack通知
        send_slack_notification(signal, result)
        
        # 統計を再計算
        recalculate_statistics()
        
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
            'body': json.dumps({
                'error': str(e)
            })
        }

def get_current_price(currency_pair):
    """外部APIから現在価格を取得"""
    # Alpha Vantage APIの例
    url = f"https://www.alphavantage.co/query"
    params = {
        'function': 'CURRENCY_EXCHANGE_RATE',
        'from_currency': currency_pair[:3],
        'to_currency': currency_pair[3:],
        'apikey': PRICE_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # レート取得
    rate = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
    return rate

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

def update_signal_result(signal_id, result):
    """DynamoDBのシグナル記録を更新"""
    table.update_item(
        Key={'signal_id': signal_id},
        UpdateExpression="""
            SET #status = :status,
                #result = :result,
                actual_exit = :exit_price,
                pnl = :pnl,
                pnl_percentage = :pnl_percentage,
                verified_at = :verified_at
        """,
        ExpressionAttributeNames={
            '#status': 'status',
            '#result': 'result'
        },
        ExpressionAttributeValues={
            ':status': 'completed' if result['result'] != 'OPEN' else 'active',
            ':result': result['result'],
            ':exit_price': Decimal(str(result['exit_price'])),
            ':pnl': Decimal(str(result['pnl'])),
            ':pnl_percentage': Decimal(str(result['pnl_percentage'])),
            ':verified_at': result['verified_at']
        }
    )

def send_slack_notification(signal, result):
    """Slack通知を送信"""
    emoji = "✅" if result['pnl'] > 0 else "❌" if result['pnl'] < 0 else "⏳"
    
    message = f"""
{emoji} Phase 1 シグナル検証結果

シグナルID: {signal['signal_id']}
通貨ペア: {signal['currency_pair']}
アクション: {signal['action']}
結果: {result['result']}

エントリー: {signal['entry_price']}
エグジット: {result['exit_price']}
損益: {result['pnl']:.1f} pips ({result['pnl_percentage']:.2f}%)

検証時刻: {result['verified_at']}
"""
    
    requests.post(SLACK_WEBHOOK, json={"text": message})

def recalculate_statistics():
    """全体統計を再計算"""
    # 全シグナルを取得
    response = table.scan(
        FilterExpression='#status = :completed',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':completed': 'completed'}
    )
    
    signals = response['Items']
    
    # 統計計算
    if signals:
        wins = [s for s in signals if float(s['pnl']) > 0]
        losses = [s for s in signals if float(s['pnl']) <= 0]
        
        win_rate = len(wins) / len(signals)
        avg_win = sum(float(s['pnl']) for s in wins) / len(wins) if wins else 0
        avg_loss = sum(abs(float(s['pnl'])) for s in losses) / len(losses) if losses else 0
        
        expected_value = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # 統計テーブルに保存
        stats_table = dynamodb.Table('phase1-statistics')
        stats_table.put_item(
            Item={
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_trades': len(signals),
                'win_rate': Decimal(str(win_rate)),
                'expected_value': Decimal(str(expected_value)),
                'avg_win': Decimal(str(avg_win)),
                'avg_loss': Decimal(str(avg_loss)),
                'updated_at': datetime.now().isoformat()
            }
        )
```

### 2. EventBridge設定

```python
# serverless.yml
service: phase1-signal-verification

provider:
  name: aws
  runtime: python3.9
  region: ap-northeast-1
  environment:
    PERFORMANCE_TABLE: ${self:custom.performanceTable}
    SLACK_WEBHOOK_URL: ${env:SLACK_WEBHOOK_URL}
    PRICE_API_KEY: ${env:PRICE_API_KEY}

functions:
  verifySignal:
    handler: handler.lambda_handler
    events:
      - eventBridge:
          eventBus: default
          pattern:
            source:
              - phase1.signals
            detail-type:
              - Signal Verification Scheduled
    iamRoleStatements:
      - Effect: Allow
        Action:
          - dynamodb:GetItem
          - dynamodb:UpdateItem
          - dynamodb:Scan
          - dynamodb:PutItem
        Resource:
          - arn:aws:dynamodb:${self:provider.region}:*:table/${self:custom.performanceTable}
          - arn:aws:dynamodb:${self:provider.region}:*:table/phase1-statistics

custom:
  performanceTable: phase1-performance

resources:
  Resources:
    PerformanceTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:custom.performanceTable}
        AttributeDefinitions:
          - AttributeName: signal_id
            AttributeType: S
        KeySchema:
          - AttributeName: signal_id
            KeyType: HASH
        BillingMode: PAY_PER_REQUEST
```

### 3. シグナル記録時のEventBridge連携

```python
# src/phase1_signal_recorder.py
import boto3
from datetime import datetime, timedelta

eventbridge = boto3.client('events')

def schedule_signal_verification(signal_id, currency_pair):
    """24時間後の検証をスケジュール"""
    
    # 24時間後の時刻を計算
    scheduled_time = datetime.now() + timedelta(hours=24)
    
    # EventBridgeにイベントを送信
    response = eventbridge.put_events(
        Entries=[
            {
                'Time': scheduled_time,
                'Source': 'phase1.signals',
                'DetailType': 'Signal Verification Scheduled',
                'Detail': json.dumps({
                    'signal_id': signal_id,
                    'currency_pair': currency_pair,
                    'scheduled_for': scheduled_time.isoformat()
                })
            }
        ]
    )
    
    print(f"Verification scheduled: {signal_id} at {scheduled_time}")
    return response
```

## デプロイ手順

### 1. 事前準備

```bash
# Serverless Frameworkインストール
npm install -g serverless

# AWS認証情報設定
aws configure

# 環境変数設定
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export PRICE_API_KEY="your_api_key"
```

### 2. デプロイ

```bash
# プロジェクトディレクトリ作成
mkdir phase1-lambda-verification
cd phase1-lambda-verification

# package.json作成
npm init -y
npm install --save-dev serverless-python-requirements

# requirements.txt作成
echo "boto3==1.26.137
requests==2.31.0" > requirements.txt

# デプロイ実行
serverless deploy
```

### 3. テスト

```bash
# Lambda関数の手動テスト
aws lambda invoke \
  --function-name phase1-signal-verification-dev-verifySignal \
  --payload '{
    "detail": {
      "signal_id": "sig_20250109_093000",
      "currency_pair": "USDJPY"
    }
  }' \
  response.json

# ログ確認
serverless logs -f verifySignal -t
```

## モニタリング

### CloudWatchダッシュボード

```python
# cloudwatch_dashboard.json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
          [".", "Errors", {"stat": "Sum"}],
          [".", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "ap-northeast-1",
        "title": "Lambda Performance"
      }
    }
  ]
}
```

### アラート設定

```yaml
# CloudWatch Alarms
LambdaErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: phase1-lambda-errors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SNSTopic
```

## コスト最適化

### 月間コスト見積もり

```
Lambda実行:
- 100シグナル/月 × 1実行/シグナル = 100実行
- 実行時間: 平均2秒
- メモリ: 128MB
- コスト: 約$0.02/月

DynamoDB:
- 読み書き: 約1000リクエスト/月
- コスト: 約$0.25/月

EventBridge:
- イベント: 100/月
- コスト: 約$0.10/月

合計: 約$0.37/月（約55円）
```

## トラブルシューティング

### よくある問題

1. **Lambda関数がタイムアウトする**
   ```bash
   # タイムアウト時間を延長
   serverless.yml:
     timeout: 30  # 30秒に設定
   ```

2. **価格APIのレート制限**
   ```python
   # リトライロジックを追加
   @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
   def get_current_price_with_retry(currency_pair):
       return get_current_price(currency_pair)
   ```

3. **DynamoDBのスロットリング**
   ```yaml
   # オンデマンドモードに変更
   BillingMode: PAY_PER_REQUEST
   ```

このシステムにより、完全自動化された24時間検証が実現します。