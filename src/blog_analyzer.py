"""
ブログ投稿用の分析モジュール（投資助言を含まない教育的内容）
"""
import logging
from pathlib import Path
from typing import Dict, Optional
from anthropic import Anthropic
from .config import CLAUDE_API_KEY
from .claude_analyzer import ClaudeAnalyzer

logger = logging.getLogger(__name__)

class BlogAnalyzer(ClaudeAnalyzer):
    """ブログ投稿用の分析クラス（投資助言を含まない）"""
    
    def __init__(self):
        super().__init__()
    
    def _create_blog_analysis_prompt(self) -> str:
        """ブログ用の分析プロンプトを作成（Volmanメソッド教育版）"""
        book_excerpt = self.book_content[:80000] if self.book_content else ""
        
        return f"""あなたはBob Volmanの「Forex Price Action Scalping」メソッドを教育的に解説する専門家です。提供されたUSD/JPY 5分足チャート画像について、Volmanの理論に基づいた教育的な解説を行ってください。

# 重要な制約事項:
- **投資助言や売買推奨は一切行わない**
- **エントリーポイント、損切り、利益確定などの具体的な売買指示は述べない**
- **「買い」「売り」「エントリー」「トレード」という言葉を推奨文脈で使わない**
- **あくまでVolmanメソッドの理論に基づいた現在のチャート状況の解説に留める**
- **将来の価格予測には必ず「（※売買は自己判断で）」を付ける**

# Volmanスキャルピングメソッド参考資料:
{book_excerpt}

# 記事構成:

## 【必須】冒頭の免責事項
「**本記事は投資判断を提供するものではありません。**FXスキャルピングの分析手法を学習する目的で、Bob Volmanの「Forex Price Action Scalping」メソッドに基づいて現在のUSD/JPYチャート状況を解説しています。実際の売買は自己責任で行ってください。」

## 1. 現在のチャート状況

### 基本情報
- 通貨ペア: USD/JPY
- 分析時刻: [日本時間]
- 現在価格: [価格]円

### 25EMA（Volman唯一の指標）の状態
- 25EMA: [価格]円
- 現在価格との位置関係: [上/下/接触]
- 25EMAの傾き: [上昇/下降/横ばい]
- Volman理論における25EMAの意味

## 2. Volmanメソッドによる解説

### Volmanの7原則の観察
1. **ダブルプレッシャー**: [現在観察されるか]
2. **ビルドアップ**: [形成状況と品質]
3. **ティーズブレイク**: [偽のブレイクの有無]
4. **ラウンドナンバー**: [心理的節目の影響]

### サポート・レジスタンスレベル
プライスアクション理論における重要な価格帯：
- 主要なサポートレベル: [価格]円付近
- 主要なレジスタンスレベル: [価格]円付近
- これらのレベルが形成された背景（過去の反発、心理的節目等）

### Volmanセットアップの識別（教育的観点）
Volmanの6つのセットアップ（A-F）の観点から：
- **パターンブレイク（A）**: [該当するか/条件]
- **プルバックリバーサル（B）**: [該当するか/条件]
- 現在のチャートは教科書的な[セットアップ名]の例

## 3. Volman理論の実践的観察

### 20/10ブラケットオーダーの概念（教育的説明）
Volmanメソッドでは固定のリスク/リワード比を使用：
- 利益確定: +20pips
- 損失限定: -10pips
- リスクリワード比: 2:1
- この固定ルールの背景と利点

### スキップルールの重要性
Volmanが強調するトレードを避けるべき条件：
- ATR < 7pips（ボラティリティ不足）
- スプレッド > 2pips
- ニュース前後10分

### Volmanセットアップ品質評価（教育的観点）
現在のチャートをVolman基準で評価：
- ⭐️⭐️⭐️⭐️⭐️ 教科書的なVolmanセットアップ
- ⭐️⭐️⭐️⭐️☆ 優秀なセットアップ
- ⭐️⭐️⭐️☆☆ 標準的なセットアップ
- ⭐️⭐️☆☆☆ スキップを検討すべき状況
- ⭐️☆☆☆☆ Volmanルールではスキップ

## 4. 理論的な展開シナリオ（※売買は自己判断で）

### Volman理論に基づく上方向シナリオ
Volmanセットアップの観点から：
- [セットアップ名]が形成された場合
- 理論上の目標: 現在価格 +20pips = [価格]円
- 25EMAがサポートとして機能する可能性
（※売買は自己判断で）

### Volman理論に基づく下方向シナリオ
別のVolmanセットアップから：
- [セットアップ名]の可能性
- 理論上の目標: 現在価格 -20pips = [価格]円
- 25EMAがレジスタンスとして機能する可能性
（※売買は自己判断で）

## 5. 学習ポイントのまとめ

### 本日のチャートから学べるVolman理論
1. **Volmanセットアップ**: [観察されたセットアップの特徴]
2. **25EMAの役割**: [トレンドバイアス、動的S/R]
3. **スキップルール**: [該当した条件があれば]

### Volmanメソッドの学習ステップ
- まずは6つのセットアップ（A-F）を識別できるように
- 20/10ブラケットオーダーの意味を理解
- スキップルールの重要性を認識

## 6. まとめ

本日のUSD/JPY 5分足チャートは、Bob Volmanの「Forex Price Action Scalping」メソッドで解説されている[主要なセットアップ]を観察する良い機会となりました。特に[具体的な観察内容]は、Volman理論を実際のチャートで確認できる貴重な事例です。

Volmanメソッドの学習において重要なのは、固定の20/10ブラケットオーダーと厳格なスキップルールの理解です。本記事で紹介したVolmanの観点を参考に、ご自身でもチャートを観察してみてください。

**再度お伝えしますが、本記事は教育目的であり、投資助言ではありません。実際の売買判断は、ご自身の責任で行ってください。**

---
*本記事はBob Volmanの「Forex Price Action Scalping」メソッドに基づいた教育的内容です。*"""
    
    def analyze_for_blog(self, chart_images: Dict[str, Path]) -> str:
        """ブログ用のチャート分析を実行"""
        try:
            logger.info("ブログ用分析を開始...")
            
            # プロンプトを準備
            prompt = self._create_blog_analysis_prompt()
            
            # メッセージの内容を構築
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
            
            # 各チャート画像を追加
            for timeframe, image_path in chart_images.items():
                logger.info(f"{timeframe}チャートを追加中...")
                
                # 画像をエンコード
                image_data = self._encode_image(str(image_path))
                
                # 画像の説明テキストを追加
                content.append({
                    "type": "text", 
                    "text": f"\n\n## {timeframe.upper()}チャート:"
                })
                
                # 画像を追加
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                })
            
            # Claude APIを呼び出し
            logger.info("Claude APIにブログ用分析を依頼中...")
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            )
            
            # 応答を取得
            analysis_result = response.content[0].text
            logger.info(f"ブログ用分析完了: {len(analysis_result)}文字")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"ブログ用分析エラー: {e}")
            raise