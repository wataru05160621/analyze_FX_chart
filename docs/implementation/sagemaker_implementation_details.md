# SageMaker実装の詳細解説

## PDFファイルの扱いについて

### 現在のシステム
```
Claude/GPT API → PDFをテキスト抽出して送信（80,000文字）
```

### SageMakerでの実装

#### ❌ PDFを直接処理できない
SageMakerのカスタムモデルは基本的に：
- **画像認識モデル**: チャート画像のパターン認識
- **テキスト生成モデル**: 分析文章の生成

PDFの内容は**事前に学習データに組み込む**必要があります。

#### ✅ 解決策：知識の内在化

```python
# 訓練データの構造
training_data = {
    "image": "chart_20240101_usdjpy.png",
    "analysis": """
    【プライスアクションの原則に基づく分析】
    1. ビルドアップ形成: 145.50でレジスタンス付近に密集
    2. ブレイクアウト条件: 上値を3回試している
    3. エントリー: 145.60突破で買い
    4. 損切り: 145.20（ビルドアップ下限）
    5. 利確: 146.50（次のレジスタンス）
    """
}
```

**PDFの知識をモデルに学習させる**ことで、推論時にPDFは不要になります。

## モデルの品質変化について

### 1. 初期段階（0-3ヶ月）
```
品質: ★★★☆☆（60-70%）
- 基本的なパターン認識
- 一般的な分析は可能
- 細かいニュアンスは不足
```

### 2. 成熟期（3-6ヶ月）
```
品質: ★★★★☆（80-90%）
- 独自のパターン学習完了
- PDFの原則を内在化
- 実践的な分析が可能
```

### 3. 継続的改善（6ヶ月以降）
```
品質: ★★★★★（90-95%）
- フィードバックループによる改善
- 市場環境への適応
- 高精度な予測
```

### 品質維持のポイント

#### 1. **定期的な再訓練**
```python
# 月1回の再訓練スケジュール
def monthly_retraining():
    # 新しいデータを追加
    new_data = collect_last_month_data()
    
    # 古いデータの一部を保持（忘却防止）
    balanced_data = balance_dataset(old_data, new_data)
    
    # 再訓練
    model.retrain(balanced_data)
```

#### 2. **フィードバックループ**
```
分析結果 → 実際の相場動向 → 精度評価 → データセット改善
```

## 教師データの管理

### 初期データセット（必須）
```
最低限必要:
- チャート画像: 1,000枚
- 分析テキスト: 1,000件
- 多様な相場状況を網羅

推奨:
- チャート画像: 10,000枚
- 期間: 過去2-3年分
- 各種パターンを含む
```

### 継続的なデータ追加

#### ❌ 間違った認識
「教師データは最初だけ」

#### ✅ 正しい運用
```python
# 継続的なデータ収集パイプライン
class DataCollectionPipeline:
    def __init__(self):
        self.data_quality_threshold = 0.8
    
    def daily_collection(self):
        # 1. 日次の分析結果を保存
        analysis_result = model.predict(chart)
        
        # 2. 実際の相場結果を記録（翌日）
        actual_movement = get_market_result()
        
        # 3. 予測精度を評価
        accuracy = evaluate_prediction(analysis_result, actual_movement)
        
        # 4. 高品質データのみ追加
        if accuracy > self.data_quality_threshold:
            add_to_training_data(chart, analysis_result, actual_movement)
```

### データ管理のベストプラクティス

#### 1. **バージョン管理**
```
datasets/
├── v1.0_initial_10k/     # 初期データセット
├── v1.1_added_bullish/   # 上昇相場データ追加
├── v1.2_added_bearish/   # 下落相場データ追加
└── v2.0_balanced_20k/    # バランス調整版
```

#### 2. **品質基準**
```python
quality_criteria = {
    "image_quality": "高解像度、ノイズなし",
    "analysis_quality": "具体的な価格、明確な根拠",
    "diversity": "様々な相場状況",
    "recency": "直近6ヶ月のデータを30%以上含む"
}
```

## 実装アーキテクチャ

### 完全なSageMakerパイプライン

```python
# 1. データ準備
class FXDataPreprocessor:
    def __init__(self):
        self.pdf_principles = self.extract_pdf_principles()
    
    def create_training_prompt(self, chart_features):
        return f"""
        {self.pdf_principles}
        チャート特徴: {chart_features}
        上記に基づいて分析を生成
        """

# 2. モデル訓練
class FXAnalysisModel:
    def __init__(self):
        # Vision Transformer for チャート理解
        self.vision_model = AutoModel.from_pretrained("google/vit-base")
        
        # LLM for 分析生成
        self.text_model = AutoModel.from_pretrained("rinna/japanese-gpt2-medium")
    
    def train(self, dataset):
        # マルチモーダル学習
        # 画像 → 特徴抽出 → テキスト生成
        pass

# 3. 推論エンドポイント
class FXAnalysisEndpoint:
    def predict(self, chart_image):
        # PDFなしで分析生成
        features = self.extract_features(chart_image)
        analysis = self.generate_analysis(features)
        return analysis
```

## コスト最適化のヒント

### 1. **スポットインスタンスの活用**
```
訓練コスト削減:
- オンデマンド: 580円/時間
- スポット: 174円/時間（70%削減）
```

### 2. **バッチ推論**
```python
# リアルタイム不要な分析はバッチ処理
def batch_analysis():
    # 深夜にまとめて処理
    # 8:00, 15:00, 21:00の分析を事前準備
    pass
```

### 3. **モデルの軽量化**
```
初期: Large Model (13B parameters)
最適化: Distilled Model (1B parameters)
性能: 95%維持、コスト80%削減
```

## まとめ

### PDFについて
- **直接渡せない**が、知識を学習させることで不要に
- より高速で一貫性のある分析が可能

### 品質について
- 初期は60-70%だが、**6ヶ月で90%以上**に向上
- 継続的な改善で**現在のAPIを超える**品質も可能

### 教師データについて
- 初期: 10,000件推奨
- 継続: 月300-500件追加
- **品質重視**で厳選することが重要

### 投資価値
- 初期投資: 5-10万円
- 6ヶ月後: 月額6,300円で無制限分析
- 1年後: **独自の高精度モデル**を保有