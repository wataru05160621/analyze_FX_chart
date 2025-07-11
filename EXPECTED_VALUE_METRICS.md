# Volmanメソッド期待値ベースの成功基準

## 📊 期待値の定義（Volman固定20/10システム）

```
期待値 = (勝率 × 20pips) - ((1-勝率) × 10pips)
```

### Volmanメソッドの特徴
- **固定リスクリワード比**: 2:1（利益20pips、損失10pips）
- **ブラケットオーダー**: エントリーと同時に利確・損切り注文
- **期待値プラスの条件**: 勝率33.4%以上で期待値プラス

## 🎯 Volmanメソッド期待値目標

### 1. **最低基準（固定20/10システム）**
- 期待値: プラス（> 0pips）
- リスクリワード比: 2:1（固定）
- 必要勝率: 33.4%以上
- 最大ドローダウン: 20%以内

### 2. **Phase別目標（Volman基準）**

#### Phase 1-2（検証期）
```
目標勝率: 35%以上
期待値 = (0.35 × 20) - (0.65 × 10) = +0.5pips/取引
月間目標: +50pips（100取引想定）
```

#### Phase 3（少額実取引）
```
目標勝率: 40%以上
期待値 = (0.40 × 20) - (0.60 × 10) = +2.0pips/取引
月間目標: +200pips（100取引想定）
```

#### Phase 4（本格運用）
```
目標勝率: 45%以上
期待値 = (0.45 × 20) - (0.55 × 10) = +3.5pips/取引
月間目標: +350pips（100取引想定）
```

## 📈 Volmanメソッドで期待値を上げる戦略

### 1. **高確率セットアップへの集中**
```python
class VolmanExpectedValueOptimizer:
    def calculate_position_size(self, entry, account_balance):
        """Volman固定システムでのポジションサイズ計算"""
        risk_per_trade = account_balance * 0.01  # 1%ルール
        pip_risk = 10  # 固定10pipsストップ
        position_size = risk_per_trade / (pip_risk * self.pip_value)
        
        # Volmanセットアップ確認
        if self.is_valid_volman_setup():
            return position_size
        return 0
    
    def is_valid_volman_setup(self):
        """Volmanの6つのセットアップ(A-F)を確認"""
        return any([
            self.is_pattern_break(),           # A
            self.is_pattern_break_pullback(), # B
            self.is_probe_reversal(),          # C
            self.is_failed_break_reversal(),  # D
            self.is_momentum_continuation(),   # E
            self.is_range_scalp()             # F
        ])
```

### 2. **スキップルールの厳守**
```python
def apply_volman_skip_rules(self):
    """Volmanスキップルールで低確率トレードを回避"""
    skip_reasons = []
    
    # ATRフィルター
    if self.current_atr < 7:
        skip_reasons.append("ATR < 7pips")
    
    # スプレッドフィルター
    if self.current_spread > 2:
        skip_reasons.append("Spread > 2pips")
    
    # ニュースフィルター
    if self.is_near_news_event(minutes=10):
        skip_reasons.append("News within 10 minutes")
    
    # アジア時間フィルター（任意）
    if self.is_asian_session() and self.current_atr < 10:
        skip_reasons.append("Low volatility Asian session")
    
    return len(skip_reasons) == 0, skip_reasons
```

### 3. **セットアップ品質の向上**
- **明確なパターン形成**: ダブルトップ/ボトムの完成
- **25EMAとの整合性**: トレンド方向と一致
- **ボリューム確認**: ブレイクアウト時の出来高増加
- **時間帯選択**: ロンドン・NY時間の重視

## 📊 Volmanメソッド期待値の計測と改善

### 1. **リアルタイム計測（固定20/10）**
```python
class VolmanExpectedValueTracker:
    def __init__(self):
        self.trades = []
        self.fixed_profit = 20  # pips
        self.fixed_loss = 10    # pips
        
    def add_trade(self, trade):
        """Volmanトレードの記録"""
        # 結果は必ず+20pipsか-10pips
        trade.pnl = self.fixed_profit if trade.is_winner else -self.fixed_loss
        self.trades.append(trade)
        
    def calculate_current_ev(self):
        """Volman固定システムの期待値計算"""
        if not self.trades:
            return None
            
        wins = [t for t in self.trades if t.is_winner]
        win_rate = len(wins) / len(self.trades)
        
        # Volman期待値計算
        expected_value = (win_rate * self.fixed_profit) - ((1-win_rate) * self.fixed_loss)
        
        # セットアップ別勝率
        setup_stats = self.calculate_setup_performance()
        
        return {
            "expected_value_pips": expected_value,
            "win_rate": win_rate,
            "required_win_rate": 0.334,  # 33.4%
            "actual_vs_required": win_rate - 0.334,
            "total_trades": len(self.trades),
            "winning_trades": len(wins),
            "losing_trades": len(self.trades) - len(wins),
            "total_pips": len(wins) * 20 - (len(self.trades) - len(wins)) * 10,
            "setup_performance": setup_stats
        }
    
    def calculate_setup_performance(self):
        """セットアップ別パフォーマンス"""
        setups = {
            'A': {'wins': 0, 'total': 0},  # Pattern Break
            'B': {'wins': 0, 'total': 0},  # Pattern Break Pullback
            'C': {'wins': 0, 'total': 0},  # Probe Reversal
            'D': {'wins': 0, 'total': 0},  # Failed Break Reversal
            'E': {'wins': 0, 'total': 0},  # Momentum Continuation
            'F': {'wins': 0, 'total': 0}   # Range Scalp
        }
        
        for trade in self.trades:
            if trade.setup_type in setups:
                setups[trade.setup_type]['total'] += 1
                if trade.is_winner:
                    setups[trade.setup_type]['wins'] += 1
        
        # 勝率計算
        for setup in setups.values():
            if setup['total'] > 0:
                setup['win_rate'] = setup['wins'] / setup['total']
                setup['expected_value'] = (setup['win_rate'] * 20) - ((1-setup['win_rate']) * 10)
            else:
                setup['win_rate'] = 0
                setup['expected_value'] = 0
                
        return setups
```

### 2. **Volmanセットアップの学習と最適化**
```python
def optimize_volman_setups(self, training_data):
    """Volmanセットアップの認識精度を最大化"""
    
    # 高勝率セットアップに重みを付ける
    for sample in training_data:
        # Volman期待値計算（固定20/10）
        setup_win_rate = sample['historical_win_rate']
        sample['expected_value'] = (setup_win_rate * 20) - ((1-setup_win_rate) * 10)
        sample['weight'] = max(0, sample['expected_value'])
    
    # Volmanセットアップ分類モデル
    def volman_classification_loss(y_true, y_pred):
        """セットアップ誤認識のペナルティ"""
        # 高期待値セットアップの見逃しに大きなペナルティ
        setup_weights = {
            'A': 1.2,  # Pattern Breakは高勝率
            'B': 1.5,  # Pattern Break Pullbackは最高勝率
            'C': 1.0,  # Probe Reversalは標準
            'D': 1.3,  # Failed Break Reversalは高勝率
            'E': 0.8,  # Momentum Continuationは低勝率
            'F': 0.7   # Range Scalpは最低勝率
        }
        return weighted_categorical_crossentropy(y_true, y_pred, setup_weights)
    
    return self.model.fit(
        training_data,
        loss=volman_classification_loss,
        sample_weight='weight'
    )
```

## 🚨 Volmanメソッドのリスク管理

### 1. **最大連続損失への対策（固定10pips損失）**
- 10連敗 = -100pips（口座の10%以下に設定）
- 1取引あたりのリスク: 最大1%
- 日次最大損失: 30pips（3連敗）でストップ
- 週次最大損失: 100pips（10連敗相当）でストップ

### 2. **Volman期待値の監視**
```python
def monitor_volman_performance(self):
    """Volmanシステムのパフォーマンス監視"""
    
    # 直近50取引の勝率
    recent_stats = self.calculate_recent_performance(last_n_trades=50)
    win_rate = recent_stats['win_rate']
    
    # Volman最低勝率チェック（33.4%）
    if win_rate < 0.334:
        self.pause_trading()
        self.send_alert(f"勝率{win_rate:.1%}が最低基準33.4%を下回りました")
    
    # セットアップ別の監視
    setup_performance = recent_stats['setup_performance']
    for setup_type, stats in setup_performance.items():
        if stats['total'] >= 10 and stats['win_rate'] < 0.25:
            self.disable_setup(setup_type)
            self.send_alert(f"セットアップ{setup_type}の勝率が25%未満")
    
    # 連続損失の監視
    if self.consecutive_losses >= 5:
        self.pause_trading()
        self.send_alert("5連敗を記録。一時停止します")
```

## 📋 Volmanメソッド成功基準のまとめ

### ❌ 一般的な基準（変動的なシステム）
- 勝率60%以上を目指す
- 利確・損切り幅が変動
- リスクリワード比が不安定
- 期待値の計算が複雑

### ✅ Volmanメソッド基準（固定20/10システム）
- **期待値**: 33.4%以上の勝率でプラス
- **リスクリワード比**: 2:1固定
- **最大ドローダウン**: 20%以内（100pips相当）
- **月間目標**: +50～350pips（フェーズによる）
- **セットアップ**: 6つの明確なパターン（A-F）
- **スキップルール**: ATR、スプレッド、ニュースフィルター

### 🎯 Volmanメソッドの利点
1. **シンプル**: 固定値により計算が単純
2. **一貫性**: 全トレードで同じリスクリワード
3. **検証しやすい**: 勝率だけで期待値が決まる
4. **心理的安定**: 利確・損切りが明確

---
**Volmanの格言**: 「勝率35%でも、固定2:1のリスクリワードなら長期的に利益が出る」

### 期待値早見表（固定20/10）
| 勝率 | 期待値(pips/取引) | 100取引の結果 |
|------|-------------------|---------------|
| 30% | -1.0 | -100pips |
| 33.4% | 0.0 | ±0pips |
| 35% | +0.5 | +50pips |
| 40% | +2.0 | +200pips |
| 45% | +3.5 | +350pips |
| 50% | +5.0 | +500pips |