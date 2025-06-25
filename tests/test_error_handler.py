"""
エラーハンドリングのテスト
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# テスト用にプロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.error_handler import (
    handle_error,
    retry_on_error,
    ErrorRecorder,
    FXAnalyzerError,
    ChartCaptureError
)

class TestHandleError:
    """エラーハンドリングデコレーターのテスト"""
    
    def test_sync_function_success(self):
        """同期関数の正常処理"""
        @handle_error()
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_sync_function_error_reraise(self):
        """同期関数でエラー発生（再発生）"""
        @handle_error(exception_type=ValueError, reraise=True)
        def test_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            test_func()
    
    def test_sync_function_error_no_reraise(self):
        """同期関数でエラー発生（再発生しない）"""
        @handle_error(exception_type=ValueError, reraise=False, default_return="default")
        def test_func():
            raise ValueError("test error")
        
        result = test_func()
        assert result == "default"
    
    @pytest.mark.asyncio
    async def test_async_function_success(self):
        """非同期関数の正常処理"""
        @handle_error()
        async def test_func():
            return "async success"
        
        result = await test_func()
        assert result == "async success"
    
    @pytest.mark.asyncio
    async def test_async_function_error(self):
        """非同期関数でエラー発生"""
        @handle_error(exception_type=ValueError, reraise=False, default_return="async default")
        async def test_func():
            raise ValueError("async test error")
        
        result = await test_func()
        assert result == "async default"

class TestRetryOnError:
    """リトライデコレーターのテスト"""
    
    def test_retry_success_on_second_attempt(self):
        """2回目で成功"""
        call_count = 0
        
        @retry_on_error(max_attempts=3, delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry test")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_all_attempts_fail(self):
        """全回数失敗"""
        @retry_on_error(max_attempts=2, delay=0.01)
        def test_func():
            raise ValueError("always fail")
        
        with pytest.raises(ValueError):
            test_func()
    
    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """非同期関数のリトライ成功"""
        call_count = 0
        
        @retry_on_error(max_attempts=3, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("async retry test")
            return "async success"
        
        result = await test_func()
        assert result == "async success"
        assert call_count == 2

class TestErrorRecorder:
    """エラーレコーダーのテスト"""
    
    def test_record_and_get_summary(self):
        """エラー記録とサマリー取得"""
        recorder = ErrorRecorder()
        
        # エラーを記録
        error1 = ValueError("test error 1")
        error2 = TypeError("test error 2")
        error3 = ValueError("test error 3")
        
        recorder.record(error1, {"stage": "test1"})
        recorder.record(error2, {"stage": "test2"})
        recorder.record(error3, {"stage": "test3"})
        
        summary = recorder.get_summary()
        
        assert summary["total_errors"] == 3
        assert summary["error_types"]["ValueError"] == 2
        assert summary["error_types"]["TypeError"] == 1
        assert len(summary["errors"]) == 3
    
    def test_clear_errors(self):
        """エラークリア"""
        recorder = ErrorRecorder()
        
        recorder.record(ValueError("test"), {})
        assert recorder.get_summary()["total_errors"] == 1
        
        recorder.clear()
        assert recorder.get_summary()["total_errors"] == 0
    
    def test_error_limit(self):
        """エラー履歴の上限（最新10件）"""
        recorder = ErrorRecorder()
        
        # 15件のエラーを記録
        for i in range(15):
            recorder.record(ValueError(f"error {i}"), {"index": i})
        
        summary = recorder.get_summary()
        assert summary["total_errors"] == 15
        assert len(summary["errors"]) == 10  # 最新10件のみ
        
        # 最新のエラーが含まれていることを確認
        last_error = summary["errors"][-1]
        assert "error 14" in last_error["message"]

class TestCustomExceptions:
    """カスタム例外のテスト"""
    
    def test_fx_analyzer_error(self):
        """FXAnalyzerError"""
        with pytest.raises(FXAnalyzerError):
            raise FXAnalyzerError("test fx error")
    
    def test_chart_capture_error(self):
        """ChartCaptureError"""
        with pytest.raises(ChartCaptureError):
            raise ChartCaptureError("chart capture failed")
        
        # 基底クラスでもキャッチできることを確認
        with pytest.raises(FXAnalyzerError):
            raise ChartCaptureError("chart capture failed")

if __name__ == "__main__":
    pytest.main([__file__])