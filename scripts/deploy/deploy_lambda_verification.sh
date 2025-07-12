#!/bin/bash

# Phase 1 Lambda自動検証システムのデプロイスクリプト

echo "=== Phase 1 Lambda自動検証システム デプロイ ==="
echo

# 1. プロジェクトディレクトリ作成
echo "1. プロジェクトディレクトリ作成..."
mkdir -p lambda/phase1-verification
cd lambda/phase1-verification

# 2. package.json作成
echo "2. package.json作成..."
cat > package.json << EOF
{
  "name": "phase1-signal-verification",
  "version": "1.0.0",
  "description": "Phase 1 Signal Verification Lambda",
  "devDependencies": {
    "serverless": "^3.34.0",
    "serverless-python-requirements": "^6.0.0"
  }
}
EOF

# 3. requirements.txt作成
echo "3. requirements.txt作成..."
cat > requirements.txt << EOF
boto3==1.26.137
requests==2.31.0
python-dateutil==2.8.2
EOF

# 4. Lambda関数作成
echo "4. Lambda関数作成..."
cat > handler.py << 'EOF'
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
EOF

# 5. serverless.yml作成
echo "5. serverless.yml作成..."
cat > serverless.yml << EOF
service: phase1-signal-verification

frameworkVersion: '3'

provider:
  name: aws
  runtime: python3.9
  region: ap-northeast-1
  stage: prod
  environment:
    PERFORMANCE_TABLE: phase1-performance
    PERFORMANCE_S3_BUCKET: fx-analysis-performance
    SLACK_WEBHOOK_URL: \${env:SLACK_WEBHOOK_URL}
    ALPHA_VANTAGE_API_KEY: \${env:ALPHA_VANTAGE_API_KEY, ''}

  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - s3:GetObject
            - s3:PutObject
          Resource:
            - arn:aws:s3:::fx-analysis-performance/*
        - Effect: Allow
          Action:
            - dynamodb:GetItem
            - dynamodb:UpdateItem
            - dynamodb:Scan
            - dynamodb:PutItem
          Resource:
            - arn:aws:dynamodb:\${self:provider.region}:*:table/phase1-performance
            - arn:aws:dynamodb:\${self:provider.region}:*:table/phase1-statistics

functions:
  verifySignal:
    handler: handler.lambda_handler
    timeout: 30
    events:
      # EventBridgeによるスケジュール実行
      - eventBridge:
          eventBus: default
          pattern:
            source:
              - phase1.signals
            detail-type:
              - Signal Verification Scheduled
    
  # 手動実行用エンドポイント
  manualVerify:
    handler: handler.lambda_handler
    timeout: 30
    events:
      - http:
          path: verify/{signalId}
          method: post
          cors: true

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true

resources:
  Resources:
    # S3バケット
    PerformanceS3Bucket:
      Type: AWS::S3::Bucket
      Properties:
        BucketName: fx-analysis-performance
        VersioningConfiguration:
          Status: Enabled
        LifecycleConfiguration:
          Rules:
            - Id: DeleteOldVersions
              Status: Enabled
              NoncurrentVersionExpirationInDays: 30
    
    # DynamoDBテーブル（オプション）
    PerformanceTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: phase1-performance
        AttributeDefinitions:
          - AttributeName: signal_id
            AttributeType: S
        KeySchema:
          - AttributeName: signal_id
            KeyType: HASH
        BillingMode: PAY_PER_REQUEST
EOF

# 6. EventBridge連携スクリプト作成
echo "6. EventBridge連携スクリプト作成..."
cd ../..
cat > src/schedule_signal_verification.py << 'EOF'
"""
シグナル検証をEventBridge経由でスケジュール
"""
import boto3
import json
from datetime import datetime, timedelta

eventbridge = boto3.client('events', region_name='ap-northeast-1')

def schedule_verification(signal_id, currency_pair='USDJPY', hours_later=24):
    """
    Lambda検証をスケジュール
    
    Args:
        signal_id: シグナルID
        currency_pair: 通貨ペア
        hours_later: 何時間後に検証するか（デフォルト24時間）
    """
    # スケジュール時刻を計算
    scheduled_time = datetime.now() + timedelta(hours=hours_later)
    
    # EventBridgeルールを作成
    rule_name = f"verify-signal-{signal_id}"
    
    # スケジュール式（cron形式）
    # 例: 2025-01-10 15:30 → cron(30 15 10 1 ? 2025)
    cron_expression = f"cron({scheduled_time.minute} {scheduled_time.hour} {scheduled_time.day} {scheduled_time.month} ? {scheduled_time.year})"
    
    try:
        # ルール作成
        eventbridge.put_rule(
            Name=rule_name,
            ScheduleExpression=cron_expression,
            State='ENABLED',
            Description=f'Verify signal {signal_id} at {scheduled_time}'
        )
        
        # ターゲット（Lambda関数）を追加
        lambda_arn = f"arn:aws:lambda:ap-northeast-1:455931011903:function:phase1-signal-verification-prod-verifySignal"
        
        eventbridge.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': '1',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'source': 'phase1.signals',
                        'detail-type': 'Signal Verification Scheduled',
                        'detail': {
                            'signal_id': signal_id,
                            'currency_pair': currency_pair,
                            'scheduled_for': scheduled_time.isoformat()
                        }
                    })
                }
            ]
        )
        
        print(f"✅ 検証スケジュール設定完了: {signal_id} at {scheduled_time}")
        
        # 一度だけ実行したら削除するように設定
        # （24時間後に自動削除）
        eventbridge.put_rule(
            Name=f"cleanup-{rule_name}",
            ScheduleExpression=f"cron({scheduled_time.minute} {scheduled_time.hour} {scheduled_time.day + 1} {scheduled_time.month} ? {scheduled_time.year})",
            State='ENABLED',
            Description=f'Cleanup rule for {rule_name}'
        )
        
        return {
            'rule_name': rule_name,
            'scheduled_time': scheduled_time.isoformat(),
            'status': 'scheduled'
        }
        
    except Exception as e:
        print(f"❌ スケジュール設定エラー: {e}")
        return {
            'error': str(e),
            'status': 'failed'
        }


# Phase 1パフォーマンス記録時に自動的に呼び出される
def integrate_with_phase1():
    """Phase 1と統合"""
    from phase1_performance_automation import Phase1PerformanceAutomation
    
    # 既存のrecord_signal関数を拡張
    original_record_signal = Phase1PerformanceAutomation.record_signal
    
    def record_signal_with_scheduling(self, signal, analysis_result):
        # 元の関数を実行
        signal_id = original_record_signal(self, signal, analysis_result)
        
        # EventBridge検証をスケジュール
        currency_pair = analysis_result.get('currency_pair', 'USDJPY')
        schedule_verification(signal_id, currency_pair)
        
        return signal_id
    
    # 関数を置き換え
    Phase1PerformanceAutomation.record_signal = record_signal_with_scheduling

if __name__ == "__main__":
    # テスト実行
    import sys
    if len(sys.argv) > 1:
        test_signal_id = sys.argv[1]
        result = schedule_verification(test_signal_id, hours_later=0.1)  # 6分後にテスト
        print(json.dumps(result, indent=2))
EOF

# 7. デプロイ準備
echo
echo "=== デプロイ準備完了 ==="
echo
echo "次のステップ："
echo
echo "1. AWS認証情報の確認:"
echo "   aws sts get-caller-identity"
echo
echo "2. 環境変数の設定:"
echo "   export SLACK_WEBHOOK_URL='${SLACK_WEBHOOK_URL}'"
echo
echo "3. Lambdaのデプロイ:"
echo "   cd lambda/phase1-verification"
echo "   npm install"
echo "   serverless deploy"
echo
echo "4. Phase 1統合の更新:"
echo "   # src/phase1_performance_automation.pyに追加"
echo "   from schedule_signal_verification import schedule_verification"
echo
echo "注意: S3バケット名 'fx-analysis-performance' は一意である必要があります。"
echo "既に使用されている場合は、serverless.ymlで別の名前に変更してください。"