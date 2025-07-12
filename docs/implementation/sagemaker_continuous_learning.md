# SageMakerでの継続学習システム

## Haikuの品質問題

確認したHaikuの分析品質：
- ❌ 通貨ペアを誤認識（USD/JPYの価格を1.1850と表示）
- ❌ 一般的すぎる分析内容
- ❌ 実際のチャートを見ていない可能性

## SageMakerでの継続学習実装

### 1. アーキテクチャ

```python
class ContinuousLearningSageMaker:
    """運用しながら学習する自己改善型システム"""
    
    def __init__(self):
        self.model = self.load_base_model()  # 初期モデル
        self.performance_tracker = PerformanceTracker()
        self.training_pipeline = TrainingPipeline()
    
    def analyze_and_learn(self, chart_data):
        # 1. 現在のモデルで分析
        prediction = self.model.predict(chart_data)
        
        # 2. 予測を記録
        prediction_id = self.save_prediction(prediction)
        
        # 3. 24時間後に結果を検証
        schedule_validation(prediction_id, hours=24)
        
        # 4. プラスの期待値を持つデータを学習セットに追加
        if expected_value > 0:
            self.add_to_training_data(chart_data, actual_result)
        
        # 5. 週次で再訓練
        if self.should_retrain():
            self.incremental_training()
        
        return prediction
```

### 2. 継続学習の仕組み

#### A. フィードバックループ
```
分析予測 → 24時間後の検証 → スコアリング → 学習データ追加
```

#### B. 段階的な期待値向上
```
初期モデル（期待値0.5%） → 1ヶ月後（期待値1.0%） → 3ヶ月後（期待値1.5%） → 6ヶ月後（期待値2.0%+）
```

#### C. 学習データの自動生成
```python
def auto_generate_training_data(self):
    """運用データから自動的に学習データを生成"""
    
    # プラスの期待値を持つ予測のみを学習
    successful_predictions = self.get_positive_expected_value_predictions()
    
    # PDFの原則と組み合わせ
    for pred in successful_predictions:
        training_sample = {
            "chart": pred.chart_image,
            "features": self.extract_features(pred.chart_data),
            "analysis": pred.analysis_text,
            "actual_outcome": pred.verified_result,
            "expected_value": pred.expected_value,
            "risk_reward_ratio": pred.risk_reward_ratio,
            "pdf_principles_applied": self.match_pdf_principles(pred)
        }
        
        self.training_data.append(training_sample)
```

### 3. 費用構造

#### A. 初期構築費用
```
初期モデル訓練:
- GPU時間: 100時間 × 580円 = 58,000円
- データ準備: 20,000円
- 合計: 約80,000円
```

#### B. 継続学習の追加費用

##### オプション1: バッチ再訓練（推奨）
```
週次再訓練:
- GPU時間: 2時間/週 × 580円 = 1,160円/週
- 月額: 約5,000円
- 年額: 約60,000円
```

##### オプション2: オンライン学習
```
リアルタイム更新:
- 常時稼働GPU: ml.g4dn.xlarge
- 月額: 約30,000円（高額）
```

##### オプション3: 差分学習（最適）
```
月次ファインチューニング:
- GPU時間: 5時間/月 × 580円 = 2,900円/月
- 年額: 約35,000円
```

### 4. 実装プラン

#### Phase 1: 基礎モデル構築（0-1ヶ月）
```python
# 初期データセット作成
initial_dataset = {
    "manual_annotations": 1000,  # 手動でラベル付け
    "pdf_principles": extract_from_pdf(),
    "historical_data": past_6_months_data
}

# ベースモデル訓練
base_model = train_vision_language_model(
    architecture="ViT + GPT2",
    dataset=initial_dataset,
    epochs=100
)
```

#### Phase 2: 自動改善システム（1-3ヶ月）
```python
class AutoImprovementPipeline:
    def daily_routine(self):
        # 朝8:00の分析実行
        predictions = self.run_morning_analysis()
        
        # 予測を保存
        self.save_predictions(predictions)
        
        # 前日の予測を検証
        yesterday_accuracy = self.validate_yesterday()
        
        # 学習データを更新
        if yesterday_accuracy > threshold:
            self.update_training_data()
    
    def weekly_retrain(self):
        # 差分データで再訓練
        new_data = self.get_week_data()
        self.model = self.incremental_train(
            base_model=self.model,
            new_data=new_data,
            epochs=10  # 少ないエポック数
        )
```

#### Phase 3: 品質監視と調整（3ヶ月以降）
```python
class QualityMonitor:
    def track_metrics(self):
        return {
            "prediction_accuracy": self.calc_accuracy(),
            "profit_factor": self.calc_profit_factor(),
            "user_feedback": self.get_feedback_score(),
            "drift_detection": self.detect_concept_drift()
        }
    
    def auto_adjust(self, metrics):
        if metrics["drift_detection"]:
            # より頻繁な再訓練
            self.increase_training_frequency()
        
        if metrics["accuracy"] < 0.8:
            # より多くのデータ収集
            self.expand_data_collection()
```

### 5. 費用比較

| 項目 | 初年度 | 2年目以降 |
|------|---------|-----------|
| **初期構築** | 80,000円 | 0円 |
| **月次再訓練** | 35,000円 | 35,000円 |
| **推論コスト** | 75,600円 | 75,600円 |
| **合計** | 190,600円 | 110,600円 |
| **月額換算** | 15,883円 | 9,217円 |

### 6. ROI分析

#### 現在のClaude API
- 月額: 15,000円
- 年額: 180,000円
- 品質: 一定

#### SageMaker継続学習
- 初年度: 190,600円（+10,600円）
- 2年目: 110,600円（-69,400円削減）
- 3年目以降: 年間69,400円削減
- **品質: 継続的に向上**

### 7. 実装の具体例

```python
# 完全な継続学習システム
class FXAnalysisContinuousLearning:
    def __init__(self):
        self.sagemaker_client = boto3.client('sagemaker')
        self.model_endpoint = self.deploy_initial_model()
        
    def analyze_with_learning(self, chart_path):
        # 1. 現在のモデルで予測
        features = self.extract_features(chart_path)
        prediction = self.predict(features)
        
        # 2. 予測を記録（後で検証用）
        prediction_record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(),
            "chart_path": chart_path,
            "prediction": prediction,
            "features": features
        }
        self.save_to_dynamodb(prediction_record)
        
        # 3. 分析結果を返す
        return self.format_analysis(prediction)
    
    def validate_and_learn(self):
        """24時間後に実行される検証と学習"""
        yesterday_predictions = self.get_yesterday_predictions()
        
        for pred in yesterday_predictions:
            # 実際の市場結果を取得
            actual = self.get_actual_market_movement(pred.timestamp)
            
            # 精度を計算
            accuracy = self.calculate_accuracy(pred.prediction, actual)
            
            # 高精度な予測は学習データに追加
            if accuracy > 0.8:
                self.add_to_training_set({
                    "features": pred.features,
                    "target": actual,
                    "quality_score": accuracy
                })
        
        # 十分なデータが溜まったら再訓練
        if self.should_retrain():
            self.trigger_retraining()
    
    def trigger_retraining(self):
        """SageMakerで増分学習を実行"""
        training_job_name = f"fx-analysis-retrain-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.sagemaker_client.create_training_job(
            TrainingJobName=training_job_name,
            AlgorithmSpecification={
                'TrainingImage': 'your-custom-training-image',
                'TrainingInputMode': 'Pipe'
            },
            RoleArn='your-sagemaker-role',
            InputDataConfig=[{
                'ChannelName': 'training',
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': 's3://your-bucket/incremental-data/',
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                }
            }],
            OutputDataConfig={
                'S3OutputPath': 's3://your-bucket/model-outputs/'
            },
            ResourceConfig={
                'InstanceType': 'ml.p3.2xlarge',
                'InstanceCount': 1,
                'VolumeSizeInGB': 30
            },
            StoppingCondition={
                'MaxRuntimeInSeconds': 7200  # 2時間まで
            },
            HyperParameters={
                'epochs': '10',
                'learning_rate': '0.0001',
                'batch_size': '32',
                'model_type': 'incremental'
            }
        )
```

## まとめ

### SageMakerで継続学習は可能

1. **初期投資**: 約80,000円
2. **継続費用**: 月額2,900円（差分学習）
3. **期待値向上**: 6ヶ月で期待値2.0%以上

### メリット
- ✅ 自動的に賢くなる
- ✅ 市場変化に適応
- ✅ 2年目から大幅コスト削減
- ✅ 独自の競争優位性

### デメリット
- ❌ 初期投資が必要
- ❌ 最初の3ヶ月は品質が低い
- ❌ 技術的な運用スキルが必要

**推奨**: 初期はClaude APIを使いながらデータを蓄積し、6ヶ月後にSageMakerに移行する段階的アプローチ