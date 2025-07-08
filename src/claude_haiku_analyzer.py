"""
Claude 3 Haiku専用アナライザー
高速・低コスト・実用的な品質
"""
import os
import logging
import base64
from pathlib import Path
from typing import Dict
from anthropic import Anthropic
from .logger import setup_logger
from .config import CLAUDE_API_KEY

logger = setup_logger(__name__)

class ClaudeHaikuAnalyzer:
    """Claude 3 Haiku専用のFXチャート分析クラス"""
    
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        self.model = "claude-3-haiku-20240307"
        
    def analyze_charts(self, chart_images: Dict[str, Path]) -> str:
        """チャート画像を分析（Haiku版）"""
        try:
            messages = [{
                "role": "user",
                "content": self._create_haiku_prompt(chart_images)
            }]
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,  # Haikuに適した設定
                temperature=0.3,  # 一貫性重視
                messages=messages
            )
            
            analysis = response.content[0].text
            
            # 使用量とコスト情報をログ
            usage = response.usage
            cost = (usage.input_tokens / 1_000_000) * 0.25 + (usage.output_tokens / 1_000_000) * 1.25
            logger.info(f"Haiku分析完了: {len(analysis)}文字, コスト: ${cost:.5f} (¥{cost*150:.2f})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Haiku分析エラー: {e}")
            raise
    
    def analyze_for_blog(self, chart_images: Dict[str, Path]) -> str:
        """ブログ用の教育的分析を生成（Haiku版）"""
        try:
            messages = [{
                "role": "user",
                "content": self._create_blog_prompt(chart_images)
            }]
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.5,  # 創造性を少し上げる
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Haikuブログ分析エラー: {e}")
            raise
    
    def _create_haiku_prompt(self, chart_images: Dict[str, Path]) -> list:
        """Haiku用の効率的なプロンプトを作成"""
        content = []
        
        # 簡潔で具体的なプロンプト
        content.append({
            "type": "text",
            "text": """FXチャート分析を実施してください。

【分析項目】
1. 環境認識
   - トレンド方向（上昇/下降/レンジ）
   - トレンド強度（5段階評価）
   - 現在価格

2. 重要価格帯
   - レジスタンス（上値抵抗線）
   - サポート（下値支持線）
   - 注目すべき価格帯

3. トレード戦略
   - エントリー：価格と根拠
   - ストップロス：価格設定
   - 利確目標：第1目標、第2目標

4. 注意事項
   - リスク要因
   - 時間帯による注意点

500文字以内で、具体的な価格を含めて分析してください。"""
        })
        
        # 画像を追加
        for timeframe, image_path in sorted(chart_images.items()):
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            })
            content.append({
                "type": "text",
                "text": f"{timeframe}チャート"
            })
        
        return content
    
    def _create_blog_prompt(self, chart_images: Dict[str, Path]) -> list:
        """ブログ用プロンプト（教育的内容）"""
        content = []
        
        content.append({
            "type": "text",
            "text": """FX初心者向けの教育的なチャート解説を作成してください。

【構成】
1. 本日の相場状況（分かりやすく）
2. チャートの見方（初心者向け）
3. 注目ポイント（なぜ重要か説明）
4. リスク管理の重要性

【トーン】
- 親しみやすく
- 専門用語は必要最小限
- 具体例を使用

600文字程度で、初心者にも理解しやすい内容にしてください。"""
        })
        
        # 1時間足チャートのみ使用（ブログ用）
        if '1hour' in chart_images:
            with open(chart_images['1hour'], "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            })
        
        return content