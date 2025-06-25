# ChatGPTプロジェクト設定の実装方法

## 概要
ChatGPTのプロジェクト機能で設定している内容をAPI経由で利用する方法

## プロジェクト設定内容
- **プロジェクトファイル**: `doc/プライスアクションの原則.pdf`
- **分析プロンプト**: 「プロジェクトファイルを参考に、画像について環境認識、トレードプランの作成をしてください。」

## 実装アプローチ

### 1. プロジェクト設定の再現
ChatGPTプロジェクトで設定している以下の内容を、APIリクエストに組み込みます：

```python
# config/analysis_config.py
CHART_ANALYSIS_SYSTEM_PROMPT = """
あなたは経験豊富なFXトレーダーです。
プライスアクションの原則に基づいて、以下の観点でチャート分析を行ってください：

1. 環境認識
   - 現在の相場環境（トレンド/レンジ）
   - 主要なサポート・レジスタンスレベル
   - 上位時間軸での位置関係
   
2. プライスアクション分析
   - ピンバー、インサイドバー、エンゴルフィングバーなどのパターン
   - スイングハイ・スイングローの識別
   - 価格の拒絶反応
   
3. トレードプラン
   - エントリーポイント
   - ストップロス設定
   - 利確目標（リスクリワード比）
   - 代替シナリオ

注意: doc/プライスアクションの原則.pdfの内容に従って分析を行ってください。
"""

# プロジェクトで使用しているカスタムインストラクション
CUSTOM_INSTRUCTIONS = {
    "analysis_style": "conservative",  # 保守的な分析
    "risk_level": "medium",
    "indicators": ["移動平均線", "RSI", "MACD"],
    "time_zones": "JST"
}
```

### 2. API実装例

```python
import openai
from datetime import datetime

class ChartAnalyzer:
    def __init__(self, api_key, system_prompt, custom_instructions):
        self.client = openai.OpenAI(api_key=api_key)
        self.system_prompt = system_prompt
        self.custom_instructions = custom_instructions
    
    def analyze_chart(self, chart_images):
        """
        チャート画像を分析
        """
        # プロジェクト設定を含むメッセージを構築
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "プロジェクトファイルを参考に、画像について環境認識、トレードプランの作成をしてください。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{chart_images['5min']}"
                        }
                    },
                    {
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:image/png;base64,{chart_images['1hour']}"
                        }
                    }
                ]
            }
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",  # または gpt-4o
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
```

### 3. プロジェクトファイルの管理

```python
# project_files/fx_analysis_rules.txt
"""
[ここにChatGPTプロジェクトで設定したルールや分析手法を記載]
例：
- フィボナッチリトレースメントの使用方法
- 特定のチャートパターンの解釈
- リスク管理ルール
"""

# プロジェクトファイルを読み込んでシステムプロンプトに追加
def load_project_files():
    with open('project_files/fx_analysis_rules.txt', 'r', encoding='utf-8') as f:
        return f.read()
```

## 必要な情報

ChatGPTプロジェクトの設定を完全に再現するために、以下の情報をご提供ください：

1. **プロジェクトで設定しているカスタムインストラクション**
2. **アップロードしているファイルの内容**（分析ルール、手法など）
3. **よく使用するプロンプトのテンプレート**
4. **特定の分析手法や指標**

これらの情報があれば、API経由でもプロジェクトと同等の分析を実行できます。