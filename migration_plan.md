# 高品質分析への段階的移行プラン

## 現状の問題
- Haikuは安いが品質が低い（通貨ペア誤認識など）
- Claude APIは高品質だが高額（月15,000円）
- 即座に高品質＋低コストは困難

## 推奨移行プラン

### Phase 1: データ収集期（0-3ヶ月）
**Claude API + データ蓄積**

```
実装:
- Claude 3.5 Sonnet（最高品質）で分析
- 全ての分析結果と市場結果を保存
- 高品質な教師データを蓄積

コスト: 月15,000円
品質: ★★★★★（最高）
```

### Phase 2: ハイブリッド期（3-6ヶ月）
**Claude + SageMaker初期モデル**

```
実装:
- 重要な分析：Claude API（朝8時のみ）
- テスト分析：SageMaker（午後）
- モデルの精度を徐々に向上

コスト: 月10,000円
品質: ★★★★☆（Claude併用で維持）
```

### Phase 3: 移行完了期（6ヶ月以降）
**SageMaker完全移行**

```
実装:
- 全ての分析をSageMakerで実行
- 継続学習で常に改善
- 独自の強みを持つモデルに

コスト: 月6,000円
品質: ★★★★★（独自進化）
```

## 具体的な実装手順

### 今すぐ開始できること

1. **データ収集スクリプトの実装**
```python
# 毎回の分析結果を構造化して保存
def save_for_future_training(analysis_result, chart_path, currency_pair):
    data = {
        "timestamp": datetime.now(),
        "currency_pair": currency_pair,
        "chart_path": chart_path,
        "analysis": analysis_result,
        "market_conditions": extract_market_conditions(),
        "price_at_analysis": get_current_price(currency_pair)
    }
    
    # S3またはローカルに保存
    save_to_storage(data)
    
    # 24時間後の検証をスケジュール
    schedule_validation(data["timestamp"])
```

2. **品質測定システム**
```python
def measure_prediction_quality(prediction, actual_result):
    metrics = {
        "direction_accuracy": check_direction(prediction, actual_result),
        "price_level_accuracy": check_price_levels(prediction, actual_result),
        "timing_accuracy": check_timing(prediction, actual_result),
        "risk_reward_achieved": check_risk_reward(prediction, actual_result)
    }
    
    return calculate_overall_score(metrics)
```

3. **教師データの自動ラベリング**
```python
def auto_label_training_data():
    # プラスの期待値を持つ予測を自動的にラベル付け
    successful_predictions = get_positive_expected_value_predictions()
    
    for pred in successful_predictions:
        training_sample = {
            "input": pred.chart_image,
            "output": improve_analysis_text(pred.original_analysis, pred.actual_outcome),
            "expected_value": pred.expected_value,
            "risk_reward_ratio": pred.risk_reward_ratio
        }
        
        add_to_training_dataset(training_sample)
```

## コスト・品質・時間のトレードオフ

| 期間 | ソリューション | 月額 | 品質 | メリット | デメリット |
|------|--------------|------|------|----------|-----------|
| 即座 | Haiku | 10円 | ★☆☆☆☆ | 超低価格 | 実用性なし |
| 即座 | Claude最適化 | 2,000円 | ★★★☆☆ | 低価格 | 品質制限 |
| 現在 | Claude通常 | 15,000円 | ★★★★★ | 最高品質 | 高額 |
| 6ヶ月後 | SageMaker | 6,000円 | ★★★★★ | 高品質＋成長 | 初期投資要 |

## 結論と推奨アクション

### 短期（今すぐ）
1. Claude APIを継続使用（品質重視）
2. 全分析結果の体系的な保存開始
3. 24時間後の検証システム構築

### 中期（3ヶ月後）
1. 蓄積データでSageMakerモデル訓練
2. ハイブリッド運用でコスト削減
3. モデル精度の継続的測定

### 長期（6ヶ月後）
1. SageMaker完全移行
2. 月6,000円で高品質維持
3. 継続学習で常に最新対応

**投資回収**: 初期投資80,000円は約8ヶ月で回収可能