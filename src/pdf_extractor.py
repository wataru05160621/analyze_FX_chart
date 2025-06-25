"""
PDFファイルからテキストを抽出するモジュール
"""
import PyPDF2
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PDFExtractor:
    """PDFファイルからテキストを抽出するクラス"""
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        
    def extract_text(self) -> str:
        """PDFからテキストを抽出"""
        try:
            text = ""
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 全ページからテキストを抽出
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                    
            logger.info(f"PDFから{len(text)}文字のテキストを抽出しました")
            return text
            
        except Exception as e:
            logger.error(f"PDF抽出エラー: {e}")
            raise
            
    def get_summary(self, max_chars: int = 5000) -> str:
        """PDFの要約を取得（文字数制限付き）"""
        full_text = self.extract_text()
        
        if len(full_text) <= max_chars:
            return full_text
            
        # 長すぎる場合は最初と最後を抽出
        half_chars = max_chars // 2
        summary = f"{full_text[:half_chars]}\n\n[... 中略 ...]\n\n{full_text[-half_chars:]}"
        
        return summary