# Phase1 検証データ構造と保存方法

## データ保存場所

```
phase1_data/
├── phase1_trades.db          # メインデータベース（SQLite）
├── json_backups/             # JSONバックアップ
│   ├── trade_YYYYMMDD_001.json
│   └── ...
├── trade_charts/             # トレードチャート画像
│   ├── entry/
│   └── exit/
├── daily_reports/            # 日次レポート（CSV）
│   ├── trades_YYYY-MM-DD.csv
│   └── stats_YYYY-MM-DD.csv
└── ml_datasets/              # 機械学習用データセット
    └── features.csv
```

## データ構造

### 1. トレード記録（TradeRecord）

```python
{
  # 基本情報
  "trade_id": "TRADE_20240315_001",
  "timestamp": "2024-03-15T08:30:00",
  "session": "アジア",  # アジア/ロンドン/NY
  
  # エントリー情報
  "setup_type": "A",  # A-F (Volmanセットアップ)
  "entry_price": 150.123,
  "entry_time": "2024-03-15T08:30:00",
  "signal_quality": 4,  # 1-5の品質評価
  
  # ビルドアップ情報
  "buildup_duration": 45,  # 分
  "buildup_pattern": "三角保ち合い",
  "ema_configuration": "上昇配列",
  
  # 市場環境
  "atr_at_entry": 8.5,
  "spread_at_entry": 1.2,
  "volatility_level": "中",
  "news_nearby": false,
  
  # 結果
  "exit_price": 150.323,
  "exit_time": "2024-03-15T09:05:00",
  "exit_reason": "TP",  # TP/SL/手動
  "pips_result": 20.0,
  "profit_loss": 2000.0,
  
  # 詳細分析
  "max_favorable_excursion": 25.0,  # 最大含み益
  "max_adverse_excursion": -5.0,    # 最大含み損
  "time_in_trade": 35,  # 分
  
  # 証跡
  "entry_chart_path": "charts/entry_001.png",
  "exit_chart_path": "charts/exit_001.png",
  "ai_analysis_summary": "良好なビルドアップからの明確なブレイク",
  "confidence_score": 0.85
}
```

### 2. 市場スナップショット（5分ごと）

```python
{
  "timestamp": "2024-03-15T08:30:00",
  "price": 150.123,
  "ema_25": 150.100,
  "ema_75": 150.050,
  "ema_200": 149.900,
  "atr": 8.5,
  "spread": 1.2,
  "volume": 12345,
  "session": "アジア",
  "major_news": ["日銀政策会合"]
}
```

### 3. パフォーマンス統計（日次）

```python
{
  "date": "2024-03-15",
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "win_rate": 60.0,
  "total_pips": 35.0,
  "profit_factor": 2.33,
  "max_drawdown": -15.0,
  "average_win": 20.0,
  "average_loss": -10.0,
  "best_setup_type": "A",
  "worst_setup_type": "D"
}
```

## 収集すべき重要データ

### 1. **エントリー時の詳細**
- ビルドアップの質（圧縮期間、形状）
- EMA配列（トレンドフォロー条件）
- ATRとスプレッド（実行可能性）
- 直近ニュースの有無

### 2. **トレード中の動き**
- 最大含み益（MFE: Maximum Favorable Excursion）
- 最大含み損（MAE: Maximum Adverse Excursion）
- 価格の動きパターン

### 3. **環境要因**
- セッション（時間帯）
- 曜日効果
- 月初/月末効果
- 重要指標との関係

### 4. **AI分析との相関**
- 事前分析の信頼度スコア
- 実際の結果との一致度
- 予測精度の向上ポイント

## データ活用方法

### 1. **日次分析**
```python
# 毎日21時に実行
collector = Phase1DataCollector()
collector.calculate_daily_stats(today)
```

### 2. **週次レポート**
```python
# 毎週日曜に実行
summary = collector.get_performance_summary(
    start_date="2024-03-11",
    end_date="2024-03-17"
)
```

### 3. **機械学習用エクスポート**
```python
# Phase 3準備
collector.export_for_ml_training(
    "ml_datasets/features_202403.csv"
)
```

## 分析の観点

### 1. **セットアップ別分析**
- どのセットアップ（A-F）が最も有効か
- 市場環境との相性
- 改善ポイントの特定

### 2. **時間帯分析**
- セッション別勝率
- ボラティリティとの関係
- 最適なトレード時間

### 3. **ビルドアップ品質分析**
- パターン別成功率
- 圧縮期間と結果の相関
- EMA配列の影響度

### 4. **リスク分析**
- MAE分布（どこまで逆行するか）
- 最適なストップロス位置
- ポジションサイジング改善

## 実装例

```python
# トレード記録
from src.phase1_data_collector import Phase1DataCollector, TradeRecord

collector = Phase1DataCollector()

# MT4からのトレード結果を記録
trade = TradeRecord(
    trade_id=f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    # ... 各フィールドを設定
)

collector.save_trade(trade)

# 定期的な市場スナップショット
snapshot = MarketSnapshot(
    timestamp=datetime.now().isoformat(),
    # ... 市場データ
)
collector.save_market_snapshot(snapshot)
```

このデータ構造により、Phase 1の検証結果を体系的に蓄積し、Phase 3のAIシグナル配信サービスの基盤となる学習データを構築できます。