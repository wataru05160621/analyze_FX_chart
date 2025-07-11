# Phase 1 パフォーマンス記録ガイド

## 概要
Phase 1のシグナル生成から結果検証までを自動化し、期待値ベースでパフォーマンスを追跡します。

## 自動化の仕組み

### 1. シグナル記録の自動化

```python
# main_multi_currency.pyに統合
from src.phase1_alert_system import SignalGenerator, TradingViewAlertSystem
from src.phase1_performance_automation import Phase1PerformanceAutomation

class Phase1Integration:
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.alert_system = TradingViewAlertSystem()
        self.performance = Phase1PerformanceAutomation()
    
    def process_analysis(self, analysis_result):
        # 1. シグナル生成
        signal = self.signal_generator.generate_trading_signal(
            analysis_result['summary']
        )
        
        # 2. アラート送信
        if signal['action'] != 'NONE':
            alert = self.alert_system.send_trade_alert({
                'signal': signal,
                'summary': analysis_result['summary']
            })
            
            # 3. パフォーマンス自動記録
            signal_id = self.performance.record_signal(signal, analysis_result)
            
            print(f"シグナル記録: {signal_id}")
```

### 2. 実行結果の記録

#### 手動取引の場合
```python
# 取引実行後に記録
performance.update_signal_execution(signal_id, {
    "entry_price": 145.52,  # 実際の約定価格
    "executed_at": "2025-01-09 09:15:00"
})
```

#### TradingView経由の場合
```python
# Webhookで自動記録
@app.route('/webhook/execution', methods=['POST'])
def record_execution():
    data = request.json
    signal_id = data['signal_id']
    
    performance.update_signal_execution(signal_id, {
        "entry_price": data['price'],
        "volume": data['volume']
    })
```

### 3. 24時間後の自動検証

```python
# AWS Lambda関数として実装
import boto3
import json

def lambda_handler(event, context):
    """24時間後に自動実行される検証"""
    signal_id = event['signal_id']
    
    performance = Phase1PerformanceAutomation()
    performance.verify_signal_result(signal_id)
    
    # 結果をSlack通知
    return {
        'statusCode': 200,
        'body': json.dumps('Verification completed')
    }
```

### 4. 日次レポートの自動生成

```python
# 毎日21時に実行
def daily_performance_report():
    performance = Phase1PerformanceAutomation()
    report = performance.generate_performance_report()
    
    # Slack/メールで送信
    send_daily_report(report)
    
    # CSVエクスポート
    csv_file = performance.export_to_csv()
    upload_to_s3(csv_file)

# cron設定
# 0 21 * * * python daily_performance_report.py
```

## セットアップ手順

### 1. 環境変数の設定

```bash
# .env.phase1に追加
PERFORMANCE_S3_BUCKET=fx-analysis-performance
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
AWS_LAMBDA_ARN=arn:aws:lambda:ap-northeast-1:...
```

### 2. AWS Lambdaの設定

```bash
# serverless.ymlの例
service: phase1-performance

provider:
  name: aws
  runtime: python3.9
  region: ap-northeast-1

functions:
  verifySignal:
    handler: handler.verify_signal
    events:
      - eventBridge:
          schedule: rate(24 hours)
    environment:
      PERFORMANCE_TABLE: ${env:PERFORMANCE_TABLE}
```

### 3. DynamoDBテーブルの作成

```python
import boto3

dynamodb = boto3.resource('dynamodb')

table = dynamodb.create_table(
    TableName='phase1-performance',
    KeySchema=[
        {
            'AttributeName': 'signal_id',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'timestamp',
            'KeyType': 'RANGE'
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'signal_id',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'timestamp',
            'AttributeType': 'S'
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)
```

## 実装の統合

### main_multi_currency.pyへの統合

```python
# 既存のコードに追加
def analyze_currency_pair(currency_pair, image_path, prices):
    """通貨ペアの分析を実行（パフォーマンス記録付き）"""
    
    # 既存の分析処理
    analysis_result = analyze_fx_chart(image_path, currency_pair, prices)
    
    # Phase 1統合
    if os.environ.get('ENABLE_PHASE1', 'false') == 'true':
        phase1 = Phase1Integration()
        phase1.process_analysis(analysis_result)
    
    return analysis_result
```

## パフォーマンス指標

### リアルタイムダッシュボード

```python
# Streamlitダッシュボード例
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def show_performance_dashboard():
    st.title("Phase 1 パフォーマンスダッシュボード")
    
    performance = Phase1PerformanceAutomation()
    stats = performance.performance_data["statistics"]
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("期待値", f"{stats['expected_value_percentage']:.2f}%")
    
    with col2:
        st.metric("リスクリワード比", f"{stats['risk_reward_ratio']:.2f}")
    
    with col3:
        st.metric("勝率", f"{stats['win_rate']:.1%}")
    
    with col4:
        st.metric("累計損益", f"{stats['total_pnl']:.1f} pips")
    
    # 資産曲線
    df = pd.DataFrame(performance.performance_data["signals"])
    df['cumulative_pnl'] = df['pnl'].cumsum()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['cumulative_pnl'],
        mode='lines',
        name='累計損益'
    ))
    
    st.plotly_chart(fig)
```

## 自動化のメリット

1. **正確なデータ収集**
   - 全シグナルを漏れなく記録
   - 実際の結果を24時間後に自動検証

2. **期待値の継続的な監視**
   - リアルタイムで期待値を計算
   - 目標を下回ったら自動アラート

3. **改善点の自動発見**
   - パフォーマンス低下を自動検出
   - 改善提案を自動生成

4. **Phase 2への移行判断**
   - 客観的なデータに基づく判断
   - 移行基準を満たしたら通知

## トラブルシューティング

### よくある問題

1. **検証が実行されない**
   ```bash
   # Lambda関数のログを確認
   aws logs tail /aws/lambda/phase1-verify-signal --follow
   ```

2. **価格データが取得できない**
   ```python
   # 価格API設定を確認
   PRICE_API_KEY=your_api_key
   PRICE_API_URL=https://api.example.com/fx/price
   ```

3. **レポートが生成されない**
   ```bash
   # 手動でレポート生成
   python -c "from src.phase1_performance_automation import *; Phase1PerformanceAutomation().generate_performance_report()"
   ```

## 次のステップ

パフォーマンスが以下の基準を満たしたら、Phase 2への移行を検討：

- 期待値: +1.0%以上を3ヶ月継続
- リスクリワード比: 1.5以上を維持
- 最大ドローダウン: 20%以内
- 総取引数: 100回以上

自動化により、客観的なデータに基づいた意思決定が可能になります。