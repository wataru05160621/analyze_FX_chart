# FX自動売買システム 段階的導入プラン

## 概要
このドキュメントは、FX分析システムから自動売買システムへの段階的な移行計画と実装設計を記載します。

## 全体アーキテクチャ

```
Phase 1: 分析 → 通知 → 手動取引
Phase 2: 分析 → API → デモ取引
Phase 3: 分析 → AWS → 少額実取引
Phase 4: 分析 → AWS → 複数通貨本格運用
```

---

## Phase 1: TradingViewアラート → 手動取引（0-2ヶ月）

### 目的
- 自動分析の精度検証
- 売買シグナルの有効性確認
- リスクなしでのシステム評価

### システム構成

```python
# src/phase1_alert_system.py
import requests
from typing import Dict

class TradingViewAlertSystem:
    """Phase 1: アラート通知システム"""
    
    def __init__(self):
        self.webhook_url = "https://hooks.slack.com/services/YOUR_WEBHOOK"
        self.tradingview_webhook = "https://your-domain.com/webhook/tradingview"
        
    def send_trade_alert(self, analysis_result: Dict):
        """分析結果から売買アラートを生成"""
        
        alert = {
            "symbol": "USD/JPY",
            "action": analysis_result['signal']['action'],  # BUY/SELL
            "entry": analysis_result['signal']['entry_price'],
            "stop_loss": analysis_result['signal']['stop_loss'],
            "take_profit": analysis_result['signal']['take_profit'],
            "confidence": analysis_result['signal']['confidence'],
            "analysis": analysis_result['summary']
        }
        
        # Slackに通知
        self._send_slack_notification(alert)
        
        # TradingViewにも送信
        self._send_to_tradingview(alert)
        
        # メール通知
        self._send_email_alert(alert)
        
        return alert
    
    def _send_slack_notification(self, alert: Dict):
        """Slack通知"""
        message = f"""
        🔔 *FX売買シグナル*
        通貨ペア: {alert['symbol']}
        アクション: {alert['action']}
        エントリー: {alert['entry']}
        損切り: {alert['stop_loss']}
        利確: {alert['take_profit']}
        信頼度: {alert['confidence']:.1%}
        
        分析: {alert['analysis']}
        """
        
        requests.post(self.webhook_url, json={"text": message})
```

### 実装タスク

1. **アラートシステム構築**
   - Slack Webhook設定
   - メール通知設定
   - TradingView連携

2. **シグナル生成ロジック**
   ```python
   def generate_trading_signal(analysis_text: str) -> Dict:
       """分析テキストから構造化シグナルを生成"""
       signal = {
           "action": "NONE",
           "entry_price": 0,
           "stop_loss": 0,
           "take_profit": 0,
           "confidence": 0
       }
       
       # キーワードベースの判定
       if "強い上昇" in analysis_text or "ブレイクアウト" in analysis_text:
           signal["action"] = "BUY"
           signal["confidence"] = 0.8
       elif "下落トレンド" in analysis_text or "売りシグナル" in analysis_text:
           signal["action"] = "SELL"
           signal["confidence"] = 0.8
       
       # 価格レベルの抽出
       # ... 実装 ...
       
       return signal
   ```

3. **パフォーマンス記録**
   ```python
   # src/performance_tracker.py
   class PerformanceTracker:
       def record_signal(self, signal: Dict):
           """シグナルを記録"""
           record = {
               "timestamp": datetime.now(),
               "signal": signal,
               "executed": False,  # 手動実行の有無
               "result": None      # 後で結果を記録
           }
           self.save_to_database(record)
   ```

### 成功基準
- 週5件以上の有効シグナル生成
- 期待値がプラス（> 0%）
- リスクリワード比1:1.5以上
- 誤シグナル率5%以下

---

## Phase 2: OANDA API → デモ自動売買（2-4ヶ月）

### 目的
- 自動売買の技術検証
- APIによる注文執行テスト
- リスクなしでの実装確認

### システム構成

```python
# src/phase2_demo_trading.py
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.contrib.requests import MarketOrderRequest

class OandaDemoTrading:
    """Phase 2: デモ口座での自動売買"""
    
    def __init__(self):
        # デモ環境のAPI設定
        self.api = API(
            access_token=os.environ['OANDA_DEMO_TOKEN'],
            environment="practice"  # デモ環境
        )
        self.account_id = os.environ['OANDA_DEMO_ACCOUNT']
        
    async def execute_demo_trade(self, signal: Dict):
        """デモ口座で取引実行"""
        
        # 1. ポジションサイズ計算（デモは固定）
        units = 10000  # 1万通貨固定
        
        # 2. 注文データ作成
        order_data = MarketOrderRequest(
            instrument="USD_JPY",
            units=units if signal['action'] == 'BUY' else -units,
            takeProfitOnFill={"price": str(signal['take_profit'])},
            stopLossOnFill={"price": str(signal['stop_loss'])}
        )
        
        # 3. 注文実行
        try:
            order = OrderCreate(self.account_id, data=order_data.data)
            response = self.api.request(order)
            
            # 4. 実行記録
            self._log_execution(signal, response)
            
            return {"status": "success", "order_id": response['orderFillTransaction']['id']}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def monitor_positions(self):
        """ポジション監視"""
        # 定期的にポジション状態を確認
        pass
```

### Lambda関数構成

```python
# lambda/trading_executor.py
import json
import boto3
from src.phase2_demo_trading import OandaDemoTrading

def lambda_handler(event, context):
    """SQSからシグナルを受け取って取引実行"""
    
    trader = OandaDemoTrading()
    
    for record in event['Records']:
        signal = json.loads(record['body'])
        
        # 取引実行
        result = trader.execute_demo_trade(signal)
        
        # 結果をDynamoDBに保存
        save_trade_result(signal, result)
    
    return {"statusCode": 200}
```

### 実装タスク

1. **OANDA API統合**
   - デモ口座開設
   - API認証設定
   - 注文執行関数

2. **AWS Lambda設定**
   ```yaml
   # serverless.yml
   functions:
     signalGenerator:
       handler: lambda/signal_generator.handler
       events:
         - schedule: 
             rate: rate(5 minutes)
             enabled: true
     
     tradeExecutor:
       handler: lambda/trading_executor.handler
       events:
         - sqs:
             arn: !GetAtt TradingQueue.Arn
   ```

3. **リスク管理（デモ版）**
   ```python
   class DemoRiskManager:
       MAX_POSITIONS = 3
       MAX_DAILY_TRADES = 10
       
       def check_trade_allowed(self, signal):
           # ポジション数チェック
           # 1日の取引回数チェック
           # 時間帯チェック
           return True
   ```

### 成功基準
- 100回以上の自動取引実行
- API エラー率1%以下
- 月間期待値+1.0%以上（デモ）
- リスクリワード比1:2以上の維持

---

## Phase 3: AWS完全統合 → 少額実取引（4-6ヶ月）

### 目的
- 実際の資金での取引開始
- 完全自動化システムの構築
- 本番環境での安定性確認

### システム構成

```python
# src/phase3_production_trading.py
import boto3
from decimal import Decimal

class ProductionTradingSystem:
    """Phase 3: 本番環境での少額取引"""
    
    def __init__(self):
        # 本番API（少額用サブアカウント）
        self.api = API(
            access_token=self._get_secret('oanda_prod_token'),
            environment="live"
        )
        self.account_id = self._get_secret('oanda_prod_account')
        
        # リスク設定（少額）
        self.max_position_size = 1000  # 1000通貨
        self.max_risk_per_trade = 1000  # 1000円
        self.daily_loss_limit = 5000    # 5000円
        
    def calculate_position_size(self, signal: Dict, current_price: float):
        """リスクベースのポジションサイズ計算"""
        
        # ストップロスまでのpips
        sl_distance = abs(current_price - signal['stop_loss']) * 100
        
        # 1000円リスクでのポジションサイズ
        position_size = self.max_risk_per_trade / sl_distance
        
        # 最大サイズでキャップ
        return min(position_size, self.max_position_size)
```

### CloudFormationテンプレート

```yaml
# infrastructure/trading_system.yaml
Resources:
  TradingStateMachine:
    Type: AWS::StepFunctions::StateMachine
    Properties:
      StateMachineName: FXTradingWorkflow
      Definition:
        Comment: "FX自動売買ワークフロー"
        StartAt: AnalyzeMarket
        States:
          AnalyzeMarket:
            Type: Task
            Resource: !GetAtt AnalyzeFunction.Arn
            Next: CheckSignal
          
          CheckSignal:
            Type: Choice
            Choices:
              - Variable: $.signal.confidence
                NumericGreaterThan: 0.8
                Next: RiskCheck
            Default: End
          
          RiskCheck:
            Type: Task
            Resource: !GetAtt RiskCheckFunction.Arn
            Next: ExecuteTrade
          
          ExecuteTrade:
            Type: Task
            Resource: !GetAtt TradeExecutorFunction.Arn
            End: true
  
  # DynamoDB for trade history
  TradeHistoryTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: fx-trade-history
      BillingMode: PAY_PER_REQUEST
      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES
      
  # SNS for alerts
  TradingAlerts:
    Type: AWS::SNS::Topic
    Properties:
      Subscription:
        - Protocol: email
          Endpoint: your-email@example.com
```

### 実装タスク

1. **本番環境セットアップ**
   - 少額専用口座開設
   - AWS Secrets Manager設定
   - 監視アラート設定

2. **Step Functions実装**
   - 取引フロー定義
   - エラーハンドリング
   - リトライロジック

3. **監視ダッシュボード**
   ```python
   # CloudWatch Dashboard
   dashboard = {
       "widgets": [
           {
               "type": "metric",
               "properties": {
                   "metrics": [
                       ["FXTrading", "PnL", {"stat": "Sum"}],
                       [".", "TradeCount", {"stat": "Sum"}],
                       [".", "ExpectedValue", {"stat": "Average"}],
                       [".", "RiskRewardRatio", {"stat": "Average"}]
                   ],
                   "period": 300,
                   "region": "ap-northeast-1",
                   "title": "Trading Performance"
               }
           }
       ]
   }
   ```

### 成功基準
- 月間最大損失5万円以内
- システム稼働率99.9%以上
- 月間期待値+1.5%以上
- 最大ドローダウン15%以内

---

## Phase 4: 複数通貨対応 → 本格運用（6ヶ月以降）

### 目的
- 複数通貨ペアでの分散投資
- リスク分散による安定収益
- スケーラブルなシステム構築

### システム構成

```python
# src/phase4_multi_currency.py
from concurrent.futures import ThreadPoolExecutor
import asyncio

class MultiCurrencyTradingSystem:
    """Phase 4: 複数通貨対応本格運用"""
    
    def __init__(self):
        self.currency_pairs = [
            "USD_JPY", "EUR_USD", "GBP_USD", 
            "AUD_USD", "EUR_JPY", "GBP_JPY"
        ]
        
        # 通貨ペアごとの設定
        self.pair_configs = {
            "USD_JPY": {
                "max_position": 10000,
                "min_confidence": 0.8,
                "spread_limit": 0.3
            },
            "EUR_USD": {
                "max_position": 10000,
                "min_confidence": 0.85,
                "spread_limit": 0.2
            }
            # ... 他の通貨ペア
        }
        
        # ポートフォリオ設定
        self.portfolio_limits = {
            "max_total_exposure": 100000,  # 10万通貨
            "max_correlation_exposure": 0.6,  # 相関60%まで
            "max_drawdown": 0.1  # 10%
        }
    
    async def analyze_all_pairs(self):
        """全通貨ペアを並列分析"""
        
        tasks = []
        for pair in self.currency_pairs:
            task = asyncio.create_task(
                self._analyze_pair(pair)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # ポートフォリオ最適化
        optimized_signals = self._optimize_portfolio(results)
        
        return optimized_signals
    
    def _optimize_portfolio(self, signals):
        """ポートフォリオレベルの最適化"""
        
        # 1. 相関分析
        correlations = self._calculate_correlations(signals)
        
        # 2. リスクパリティ配分
        allocations = self._risk_parity_allocation(
            signals, correlations
        )
        
        # 3. 最終シグナル調整
        return self._adjust_signals(signals, allocations)
```

### Kubernetes構成

```yaml
# k8s/trading_deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fx-trading-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fx-trading
  template:
    metadata:
      labels:
        app: fx-trading
    spec:
      containers:
      - name: trading-engine
        image: your-ecr-repo/fx-trading:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        env:
        - name: TRADING_MODE
          value: "PRODUCTION"
        - name: MAX_RISK
          value: "0.02"
---
apiVersion: v1
kind: Service
metadata:
  name: fx-trading-service
spec:
  selector:
    app: fx-trading
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fx-trading-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fx-trading-system
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 実装タスク

1. **マルチカレンシー対応**
   - 通貨ペアごとの最適化
   - 相関リスク管理
   - ポートフォリオ配分

2. **高可用性実装**
   - Kubernetes展開
   - 自動スケーリング
   - 障害時フェイルオーバー

3. **高度なリスク管理**
   ```python
   class AdvancedRiskManagement:
       def portfolio_risk_check(self, positions, new_signal):
           # VaR計算
           var = self.calculate_var(positions)
           
           # ストレステスト
           stress = self.stress_test(positions, scenarios=[
               "flash_crash",
               "interest_rate_shock",
               "correlation_breakdown"
           ])
           
           # 最大ドローダウン予測
           max_dd = self.predict_max_drawdown(positions)
           
           return all([
               var < self.var_limit,
               stress.worst_case > self.stress_limit,
               max_dd < self.drawdown_limit
           ])
   ```

### 成功基準
- 月間期待値+2.0%以上
- 最大ドローダウン20%以内
- リスクリワード比1:2.5以上
- 安定した資産成長曲線

---

## 実装スケジュール

| Phase | 期間 | 主要タスク | 投資額 | 期待リターン |
|-------|------|-----------|--------|-------------|
| 1 | 0-2ヶ月 | アラート構築 | 0円 | 検証のみ |
| 2 | 2-4ヶ月 | デモ取引 | 1万円 | 検証のみ |
| 3 | 4-6ヶ月 | 少額実取引 | 10万円 | 月3-5% |
| 4 | 6ヶ月〜 | 本格運用 | 100万円〜 | 月5-10% |

## リスク管理方針

1. **段階的拡大**
   - 各フェーズで検証
   - 問題があれば前フェーズに戻る

2. **損失限定**
   - 日次損失限度額設定
   - 月次損失限度額設定

3. **継続的改善**
   - 全取引記録の分析
   - モデルの定期更新

## 次のステップ

1. Phase 1のアラートシステム実装開始
2. OANDA デモ口座開設
3. AWS環境の準備
4. 監視体制の構築