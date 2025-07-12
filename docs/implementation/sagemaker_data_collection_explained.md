# SageMaker学習データ収集の仕組み

## 追加出力は不要

現在の運用をそのまま続けながら、バックグラウンドでデータを収集します。

## 現在の出力（変更なし）

```
1. Notion → 分析結果（現状通り）
2. ブログ → 教育的記事（現状通り）
3. X → 要約投稿（現状通り）
```

## 自動的に収集されるデータ

### 1. 運用中に自動保存されるもの

```python
class CurrentSystem:
    def analyze_fx_charts(self):
        # 1. チャート生成（現状通り）
        charts = generate_charts()
        
        # 2. Claude分析（現状通り）
        analysis = claude.analyze(charts)
        
        # 3. 各種投稿（現状通り）
        notion.save(analysis)
        blog.post(analysis)
        twitter.post(summary)
        
        # 4. 【追加】バックグラウンドで学習データとして保存
        self.save_for_learning({
            "timestamp": now(),
            "charts": charts,
            "analysis": analysis,
            "currency_pair": "USD/JPY"
        })  # ← これだけ追加
```

### 2. 24時間後に自動収集されるもの

```python
def collect_actual_results():
    """cronで24時間後に自動実行"""
    
    # 昨日の予測を取得
    yesterday_predictions = get_yesterday_predictions()
    
    for pred in yesterday_predictions:
        # 実際の市場結果を取得
        actual = {
            "price_movement": get_actual_price_change(),
            "prediction_accuracy": calculate_accuracy(),
            "hit_targets": check_if_targets_hit()
        }
        
        # 学習データとして保存
        if actual["prediction_accuracy"] > 0.8:
            save_training_data(pred, actual)
```

## データ収集の具体例

### 朝8:00の通常運用

```
1. USD/JPY分析実行
   ↓
2. Notionに保存（ユーザー向け）
   ↓
3. ブログ投稿（ユーザー向け）
   ↓
4. 内部的にデータ保存（自動）← 追加作業なし
```

### 保存されるデータ構造

```json
{
  "id": "2024-07-08-08:00-USDJPY",
  "input": {
    "chart_5min": "s3://bucket/charts/usdjpy_5min_20240708.png",
    "chart_1hour": "s3://bucket/charts/usdjpy_1hour_20240708.png",
    "timestamp": "2024-07-08T08:00:00Z",
    "price": 145.50
  },
  "output": {
    "analysis": "現在の分析テキスト...",
    "predictions": {
      "direction": "up",
      "target": 146.00,
      "stop_loss": 145.20
    }
  },
  "validation": {
    "checked_at": "2024-07-09T08:00:00Z",
    "actual_price": 145.85,
    "accuracy": 0.85,
    "quality_score": "high"
  }
}
```

## 実装に必要な変更

### 最小限の追加コード

```python
# main.pyに追加するだけ
from src.training_data_collector import TrainingDataCollector

collector = TrainingDataCollector()

# 既存の分析処理
async def analyze_fx_charts():
    # ... 既存の処理 ...
    
    # 分析完了後に1行追加
    collector.save_for_future_training(
        charts=screenshots,
        analysis=analysis_result,
        currency=currency_pair
    )
    
    # ... 既存の処理続行 ...
```

### データ収集クラス

```python
class TrainingDataCollector:
    def __init__(self):
        self.storage = S3Storage()  # またはローカル
        
    def save_for_future_training(self, charts, analysis, currency):
        """バックグラウンドで保存（ユーザーには見えない）"""
        
        # 非同期で保存（メイン処理をブロックしない）
        asyncio.create_task(self._save_async({
            "timestamp": datetime.now(),
            "charts": charts,
            "analysis": analysis,
            "currency": currency,
            "status": "pending_validation"
        }))
    
    async def validate_yesterday_predictions(self):
        """24時間後に実行される検証タスク"""
        
        yesterday_data = self.get_yesterday_predictions()
        
        for data in yesterday_data:
            # 実際の結果を取得
            actual_result = self.get_market_result(data.currency)
            
            # 精度を計算
            accuracy = self.calculate_accuracy(
                predicted=data.analysis,
                actual=actual_result
            )
            
            # 高品質なデータのみ保存
            if accuracy > 0.8:
                data["validation"] = {
                    "accuracy": accuracy,
                    "actual_result": actual_result,
                    "quality": "high"
                }
                
                self.save_as_training_data(data)
```

## メリット

1. **ユーザー体験は変わらない**
   - 現在と同じ出力
   - 追加の作業なし
   - 処理時間も変わらない

2. **自動的にデータ蓄積**
   - 6ヶ月で約900件の検証済みデータ
   - 高品質なデータのみ選別
   - 人手によるラベリング不要

3. **コストゼロでデータ収集**
   - 追加のAPI呼び出しなし
   - 既存の分析結果を再利用
   - ストレージ代のみ（月100円程度）

## まとめ

**Q: 学習用の追加出力が必要？**
**A: いいえ、現在の出力をそのまま使います**

やること：
1. 既存コードに数行追加
2. バックグラウンドでデータ保存
3. 24時間後に自動検証

ユーザーから見て：
- 何も変わらない
- 追加作業なし
- 同じ品質の分析

これで6ヶ月後にはSageMaker訓練に十分なデータが自動的に揃います。