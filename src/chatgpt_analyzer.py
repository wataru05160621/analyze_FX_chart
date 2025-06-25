"""
ChatGPT APIを使用してチャート分析を行うモジュール
"""
import base64
from pathlib import Path
from typing import Dict, List
import logging
from openai import OpenAI
from .config import (
    OPENAI_API_KEY, 
    CHATGPT_MODEL, 
    MAX_TOKENS, 
    TEMPERATURE,
    ANALYSIS_PROMPT,
    PRICE_ACTION_PDF
)
from .pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)

class ChartAnalyzer:
    """ChatGPT APIを使用したチャート分析クラス"""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """PDFの内容を含むシステムプロンプトを作成"""
        base_prompt = """
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

"""
        
        # PDFの内容を追加
        try:
            pdf_extractor = PDFExtractor(PRICE_ACTION_PDF)
            pdf_content = pdf_extractor.get_summary(max_chars=3000)
            base_prompt += f"\n【プライスアクションの原則】\n{pdf_content}\n"
        except Exception as e:
            logger.warning(f"PDFの読み込みに失敗しました: {e}")
            
        return base_prompt
        
    def _encode_image(self, image_path: Path) -> str:
        """画像をbase64エンコード"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def analyze_charts(self, chart_images: Dict[str, Path]) -> str:
        """チャート画像を分析"""
        try:
            # メッセージを構築
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
                            "text": ANALYSIS_PROMPT
                        }
                    ]
                }
            ]
            
            # 画像を追加
            for timeframe, image_path in chart_images.items():
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{self._encode_image(image_path)}",
                        "detail": "high"
                    }
                })
                
            # API呼び出し
            response = self.client.chat.completions.create(
                model=CHATGPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            
            analysis_result = response.choices[0].message.content
            logger.info(f"分析完了: {len(analysis_result)}文字")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"チャート分析エラー: {e}")
            raise