# Phase 2: XMTrading (MT5) 実装計画

## 概要
Phase 2では、XMTradingのMT5を使用して自動売買システムを実装します。

## アーキテクチャ

```
Phase 1 (完了)          Phase 2 (XMTrading)
┌─────────────┐       ┌──────────────┐
│ FX分析      │       │   MT5        │
│ シグナル生成 │  -->  │   Python     │
│ Slack通知   │       │   Bridge     │
└─────────────┘       └──────────────┘
                            ↓
                      ┌──────────────┐
                      │ XMTrading    │
                      │ デモ/実口座  │
                      └──────────────┘
```

## 実装方法

### 方法1: MetaTrader5 Pythonパッケージ（推奨）

```python
# インストール
pip install MetaTrader5

# 実装例
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

class XMTradingConnector:
    def __init__(self):
        # MT5初期化
        if not mt5.initialize():
            print("MT5初期化失敗")
            return
        
        # XMTradingデモ口座にログイン
        account = 12345678  # デモ口座番号
        password = "your_password"
        server = "XMTrading-Demo"
        
        if not mt5.login(account, password=password, server=server):
            print("ログイン失敗")
            return
    
    def execute_trade(self, signal):
        """Phase 1のシグナルを受けて取引実行"""
        
        symbol = "USDJPY"
        
        # 買い注文
        if signal['action'] == 'BUY':
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,  # 0.01ロット
                "type": mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(symbol).ask,
                "sl": signal['stop_loss'],
                "tp": signal['take_profit'],
                "deviation": 20,
                "magic": 234000,
                "comment": "Phase2 auto trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
        
        # 売り注文
        elif signal['action'] == 'SELL':
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,
                "type": mt5.ORDER_TYPE_SELL,
                "price": mt5.symbol_info_tick(symbol).bid,
                "sl": signal['stop_loss'],
                "tp": signal['take_profit'],
                "deviation": 20,
                "magic": 234000,
                "comment": "Phase2 auto trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
        
        # 注文送信
        result = mt5.order_send(request)
        return result
```

### 方法2: Webhook経由でEAと連携

```python
# Phase 1側: シグナルをWebhookで送信
class MT5WebhookSender:
    def send_signal_to_mt5(self, signal):
        webhook_data = {
            "action": signal['action'],
            "symbol": "USDJPY",
            "entry": signal['entry_price'],
            "sl": signal['stop_loss'],
            "tp": signal['take_profit'],
            "lot": 0.01
        }
        
        # MT5側のWebhookレシーバーに送信
        requests.post("http://your-mt5-server/webhook", json=webhook_data)
```

## 実装手順

### 1. 環境準備
```bash
# Windows VPSまたはローカル環境
1. MT5をインストール
2. XMTradingデモ口座を開設
3. Python環境構築
```

### 2. Phase 1との統合
```python
# Phase 1のシグナルを受信して自動実行
from src.phase1_alert_system import SignalGenerator
from src.phase2_xmtrading_connector import XMTradingConnector

class Phase2Integration:
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.mt5_connector = XMTradingConnector()
        self.risk_manager = Phase2RiskManager()
        
    def process_analysis(self, analysis_text):
        # Phase 1: シグナル生成
        signal = self.signal_generator.generate_trading_signal(analysis_text)
        
        # Phase 2: リスクチェック
        if self.risk_manager.check_risk(signal):
            # MT5で自動実行
            result = self.mt5_connector.execute_trade(signal)
            return result
```

### 3. 実装ファイル構成
```
src/
├── phase2_xmtrading_connector.py  # MT5接続
├── phase2_trade_executor.py        # 取引実行
└── phase2_risk_manager.py          # リスク管理

tests/
└── test_phase2_xmtrading.py        # テストコード
```

## リスク管理（期待値ベース）

```python
class Phase2RiskManager:
    def __init__(self):
        self.max_positions = 3
        self.max_lot_size = 0.1
        self.max_daily_loss = 5000  # 円
        self.min_expected_value = 0.005  # 最低期待値0.5%
        self.min_risk_reward = 1.5  # 最低リスクリワード比
        
    def check_risk(self, signal):
        # 期待値チェック
        expected_value = self.calculate_expected_value(signal)
        if expected_value < self.min_expected_value:
            return False
            
        # リスクリワード比チェック
        risk_reward = self.calculate_risk_reward(signal)
        if risk_reward < self.min_risk_reward:
            return False
        
        # ポジション数チェック
        positions = mt5.positions_get()
        if len(positions) >= self.max_positions:
            return False
        
        # 日次損失チェック
        daily_pnl = self.calculate_daily_pnl()
        if daily_pnl < -self.max_daily_loss:
            return False
        
        return True
    
    def calculate_expected_value(self, signal):
        """期待値を計算"""
        # 過去のデータから勝率と平均損益を計算
        stats = self.get_historical_stats(signal['currency_pair'])
        
        expected_value = (
            stats['win_rate'] * stats['avg_win'] - 
            (1 - stats['win_rate']) * stats['avg_loss']
        )
        return expected_value
    
    def calculate_risk_reward(self, signal):
        """リスクリワード比を計算"""
        risk = abs(signal['entry_price'] - signal['stop_loss'])
        reward = abs(signal['take_profit'] - signal['entry_price'])
        return reward / risk if risk > 0 else 0
```

## 成功基準（期待値ベース）

### デモ期間（1-2ヶ月）
- 取引回数: 100回以上
- 期待値: +0.5%以上/取引
- リスクリワード比: 平均1.5以上
- 最大ドローダウン: 10%以内

### 少額実取引（3-4ヶ月）
- 初期資金: 10万円
- 期待値: +1.0%以上/取引
- リスクリワード比: 平均2.0以上
- 月間利益: 期待値ベースで安定

## スケジュール

1. **Week 1**: XMTradingデモ口座設定とMT5環境構築
2. **Week 2**: Python-MT5連携の実装
3. **Week 3**: 期待値ベースのリスク管理実装
4. **Week 4**: Phase 1との統合とテスト

## メリット

1. **高レバレッジ**: 少額資金で開始可能
2. **豊富な通貨ペア**: 主要通貨ペアすべて対応
3. **24時間取引**: 暗号通貨も取引可能
4. **日本語サポート**: 充実したサポート体制

## 注意事項

1. **Windows推奨**: MT5はWindows環境が最も安定
2. **VPS利用推奨**: 24時間稼働にはVPS必要
3. **API制限**: MT5 APIには一部制限あり
4. **期待値重視**: 勝率ではなく期待値を最優先

## パフォーマンス追跡

```python
class PerformanceTracker:
    """期待値ベースのパフォーマンス追跡"""
    
    def track_trade(self, trade):
        metrics = {
            "expected_value": self.calculate_ev(trade),
            "risk_reward_achieved": trade.profit / abs(trade.loss) if trade.loss != 0 else 0,
            "win": trade.profit > 0,
            "pnl": trade.profit
        }
        
        self.update_running_metrics(metrics)
        
    def get_performance_summary(self):
        """期待値ベースのサマリー"""
        return {
            "total_trades": self.total_trades,
            "current_expected_value": self.running_ev,
            "average_risk_reward": self.avg_risk_reward,
            "win_rate": self.wins / self.total_trades,
            "profit_factor": self.gross_profit / abs(self.gross_loss) if self.gross_loss != 0 else 0,
            "max_drawdown": self.max_drawdown
        }
```

期待値を重視したXMTrading実装により、安定した利益を目指します。