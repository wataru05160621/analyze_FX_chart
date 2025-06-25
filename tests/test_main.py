"""
メイン機能のテスト
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# テスト用にプロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import analyze_fx_charts, _validate_configuration
from src.error_handler import ConfigurationError, ChartCaptureError

class TestValidateConfiguration:
    """設定検証のテスト"""
    
    def test_valid_configuration_web_chatgpt(self):
        """Web版ChatGPTの有効な設定"""
        with patch.multiple(
            'src.main',
            USE_WEB_CHATGPT=True,
            ANALYSIS_PROMPT="test prompt",
            SCREENSHOT_DIR=Path("/tmp"),
            CHATGPT_EMAIL="test@example.com",
            CHATGPT_PASSWORD="password",
            CHATGPT_PROJECT_NAME="test project"
        ):
            # エラーが発生しないことを確認
            _validate_configuration()
    
    def test_valid_configuration_api_chatgpt(self):
        """API版ChatGPTの有効な設定"""
        with patch.multiple(
            'src.main',
            USE_WEB_CHATGPT=False,
            ANALYSIS_PROMPT="test prompt",
            SCREENSHOT_DIR=Path("/tmp")
        ), patch('src.config.OPENAI_API_KEY', 'test_api_key'):
            # エラーが発生しないことを確認
            _validate_configuration()
    
    def test_missing_web_chatgpt_config(self):
        """Web版ChatGPTの設定不足"""
        with patch.multiple(
            'src.main',
            USE_WEB_CHATGPT=True,
            ANALYSIS_PROMPT="test prompt",
            SCREENSHOT_DIR=Path("/tmp"),
            CHATGPT_EMAIL="",  # 空の値
            CHATGPT_PASSWORD="password",
            CHATGPT_PROJECT_NAME="test project"
        ):
            with pytest.raises(ConfigurationError):
                _validate_configuration()

@pytest.mark.asyncio
class TestAnalyzeFXCharts:
    """FXチャート分析のテスト"""
    
    async def test_successful_analysis(self):
        """正常な分析処理"""
        mock_screenshots = {"5min": Path("/tmp/test.png"), "1hour": Path("/tmp/test2.png")}
        mock_analysis = "テスト分析結果"
        
        with patch('src.main._validate_configuration'), \
             patch('src.main.TradingViewScraper') as mock_scraper_class, \
             patch('src.main.ChartAnalyzer') as mock_analyzer_class, \
             patch('src.main.NotionWriter') as mock_notion_class, \
             patch('src.main.USE_WEB_CHATGPT', False):
            
            # スクレイパーのモック
            mock_scraper = AsyncMock()
            mock_scraper.capture_charts.return_value = mock_screenshots
            mock_scraper_class.return_value = mock_scraper
            
            # アナライザーのモック
            mock_analyzer = Mock()
            mock_analyzer.analyze_charts.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer
            
            # Notionライターのモック
            mock_notion = Mock()
            mock_notion.create_analysis_page.return_value = "test_page_id"
            mock_notion_class.return_value = mock_notion
            
            result = await analyze_fx_charts()
            
            assert result["status"] == "success"
            assert result["screenshots"] == mock_screenshots
            assert result["analysis"] == mock_analysis
            
            # メソッドが呼ばれたことを確認
            mock_scraper.setup.assert_called_once()
            mock_scraper.navigate_to_chart.assert_called_once()
            mock_scraper.capture_charts.assert_called_once()
            mock_scraper.close.assert_called_once()
            mock_analyzer.analyze_charts.assert_called_once_with(mock_screenshots)
            mock_notion.create_analysis_page.assert_called_once()
    
    async def test_chart_capture_error(self):
        """チャート取得エラー"""
        with patch('src.main._validate_configuration'), \
             patch('src.main.TradingViewScraper') as mock_scraper_class:
            
            mock_scraper = AsyncMock()
            mock_scraper.capture_charts.return_value = {}  # 空の結果
            mock_scraper_class.return_value = mock_scraper
            
            result = await analyze_fx_charts()
            
            assert result["status"] == "error"
            assert "チャート取得エラー" in result["error"]
    
    async def test_analysis_error(self):
        """分析エラー"""
        mock_screenshots = {"5min": Path("/tmp/test.png")}
        
        with patch('src.main._validate_configuration'), \
             patch('src.main.TradingViewScraper') as mock_scraper_class, \
             patch('src.main.ChartAnalyzer') as mock_analyzer_class, \
             patch('src.main.USE_WEB_CHATGPT', False):
            
            # スクレイパーのモック
            mock_scraper = AsyncMock()
            mock_scraper.capture_charts.return_value = mock_screenshots
            mock_scraper_class.return_value = mock_scraper
            
            # アナライザーでエラー発生
            mock_analyzer = Mock()
            mock_analyzer.analyze_charts.side_effect = Exception("分析失敗")
            mock_analyzer_class.return_value = mock_analyzer
            
            result = await analyze_fx_charts()
            
            assert result["status"] == "error"
            assert "分析エラー" in result["error"]
    
    async def test_notion_error_continues(self):
        """Notionエラーが発生しても処理が続行される"""
        mock_screenshots = {"5min": Path("/tmp/test.png")}
        mock_analysis = "テスト分析結果"
        
        with patch('src.main._validate_configuration'), \
             patch('src.main.TradingViewScraper') as mock_scraper_class, \
             patch('src.main.ChartAnalyzer') as mock_analyzer_class, \
             patch('src.main.NotionWriter') as mock_notion_class, \
             patch('src.main.USE_WEB_CHATGPT', False):
            
            # スクレイパーのモック
            mock_scraper = AsyncMock()
            mock_scraper.capture_charts.return_value = mock_screenshots
            mock_scraper_class.return_value = mock_scraper
            
            # アナライザーのモック
            mock_analyzer = Mock()
            mock_analyzer.analyze_charts.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer
            
            # Notionでエラー発生
            mock_notion = Mock()
            mock_notion.create_analysis_page.side_effect = Exception("Notion失敗")
            mock_notion_class.return_value = mock_notion
            
            result = await analyze_fx_charts()
            
            # Notionエラーが発生しても成功扱い
            assert result["status"] == "success"
            assert result["screenshots"] == mock_screenshots
            assert result["analysis"] == mock_analysis

if __name__ == "__main__":
    pytest.main([__file__])