# Volmanメソッド分析システム設定

## 概要
Bob Volmanの「Forex Price Action Scalping」メソッドに基づくAI分析システムの設定

## Volmanメソッド設定内容
- **参考資料**: `doc/プライスアクションの原則/` 内のマークダウンファイル
- **分析プロンプト**: 「Volmanメソッドに基づき、USD/JPY 5分足チャートを6つのセットアップ(A-F)で分析してください。」

## 実装アプローチ

### 1. Volmanメソッド設定の実装
Volmanメソッドの以下の内容をシステムに組み込みます：

```python
# config/volman_config.py
VOLMAN_ANALYSIS_SYSTEM_PROMPT = """
あなたはBob Volmanのスキャルピングメソッドの専門家です。
USD/JPY 5分足チャートをVolmanメソッドに基づいて分析してください：

1. Volmanセットアップの識別
   - パターンブレイク（A）
   - パターンブレイクプルバック（B）
   - プローブリバーサル（C）
   - フェイルドブレイクリバーサル（D）
   - モメンタム継続（E）
   - レンジスキャルプ（F）
   
2. 25EMA分析
   - 価格との位置関係
   - トレンドバイアスの判定
   - 動的サポート/レジスタンス
   
3. 20/10ブラケットオーダー
   - エントリー価格: XXX.XXX
   - 利益確定: +20pips
   - ストップロス: -10pips
   - リスクリワード比: 2:1（固定）

4. スキップルール
   - ATR < 7pipsの場合はトレード禁止
   - スプレッド > 2pipsの場合はトレード禁止
   - ニュース前後10分はトレード禁止
"""

# Volmanメソッド設定
VOLMAN_SETTINGS = {
    "currency_pair": "USD/JPY",
    "timeframe": "5min",
    "indicator": "25EMA",  # Volman唯一の指標
    "profit_target": 20,  # pips
    "stop_loss": 10,  # pips
    "risk_reward": "2:1",
    "min_atr": 7,  # pips
    "max_spread": 2,  # pips
    "news_buffer": 10  # minutes
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