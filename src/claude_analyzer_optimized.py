"""
Claude APIを使用してFXチャートを分析するモジュール（最適化版）
トークン使用量を大幅に削減
"""
import os
import logging
import base64
from pathlib import Path
from typing import Dict
from anthropic import Anthropic
from .logger import setup_logger
from .pdf_extractor import PDFExtractor
from .config import CLAUDE_API_KEY

logger = setup_logger(__name__)

class ClaudeAnalyzerOptimized:
    """最適化版Claude APIを使用したチャート分析クラス"""
    
    def __init__(self):
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"
        
        # PDFから重要部分のみ抽出（10,000文字に制限）
        self.pdf_content = self._load_optimized_pdf_content()
        
    def _load_optimized_pdf_content(self) -> str:
        """PDFから重要部分のみを抽出（トークン削減）"""
        try:
            extractor = PDFExtractor()
            # 重要なセクションのみ抽出
            important_sections = [
                "ブレイクアウトの条件",
                "ビルドアップの識別",
                "エントリーポイント",
                "利益確定",
                "損切り",
                "トレンドの見極め方"
            ]
            
            content = ""
            for section in important_sections:
                section_content = extractor.extract_section(section)
                if section_content:
                    content += f"\n## {section}\n{section_content[:1500]}\n"
            
            # 最大10,000文字に制限
            return content[:10000]
        except Exception as e:
            logger.warning(f"PDF最適化エラー: {e}")
            return "プライスアクション分析の基本原則に基づいて分析してください。"
    
    def analyze_charts(self, chart_images: Dict[str, Path]) -> str:
        """チャート画像を分析（最適化版）"""
        try:
            messages = [{
                "role": "user",
                "content": self._create_optimized_prompt(chart_images)
            }]
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,  # 4000から削減
                messages=messages,
                temperature=0.3
            )
            
            analysis = response.content[0].text
            logger.info(f"最適化版Claude分析完了: {len(analysis)}文字")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Claude分析エラー: {e}")
            raise
    
    def _create_optimized_prompt(self, chart_images: Dict[str, Path]) -> list:
        """最適化されたプロンプトを作成"""
        content = []
        
        # 簡潔なプロンプト（1,000文字程度）
        content.append({
            "type": "text",
            "text": f"""FXチャート分析を実施してください。

【分析手順】
1. トレンド判定（上昇/下降/レンジ）
2. 重要価格帯の特定
3. エントリーポイントの提案
4. リスク管理（損切り・利確）

【参考原則】
{self.pdf_content[:3000]}  # PDFの重要部分のみ

【出力形式】
- 環境認識：200文字
- エントリー戦略：300文字
- リスク管理：200文字
- 総評：300文字

簡潔で実践的な分析をお願いします。"""
        })
        
        # 画像を追加（圧縮版）
        for timeframe, image_path in sorted(chart_images.items()):
            compressed_image = self._compress_image(image_path)
            if compressed_image:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": compressed_image
                    }
                })
                content.append({
                    "type": "text",
                    "text": f"{timeframe}チャート"
                })
        
        return content
    
    def _compress_image(self, image_path: Path) -> str:
        """画像を圧縮してBase64エンコード"""
        try:
            from PIL import Image
            import io
            
            # 画像を開いて圧縮
            with Image.open(image_path) as img:
                # リサイズ（最大1280x720）
                img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
                
                # 圧縮して保存
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True, quality=85)
                buffer.seek(0)
                
                # Base64エンコード
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
                
        except Exception as e:
            logger.warning(f"画像圧縮エラー: {e}")
            # 圧縮失敗時は元の画像を使用
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')