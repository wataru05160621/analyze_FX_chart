"""
エラーハンドリングモジュール
"""
import functools
import asyncio
from typing import Any, Callable, Optional, Type
import logging
from datetime import datetime
import traceback

from .logger import logger

class FXAnalyzerError(Exception):
    """FXアナライザーの基本エラークラス"""
    pass

class ChartCaptureError(FXAnalyzerError):
    """チャート取得エラー"""
    pass

class AnalysisError(FXAnalyzerError):
    """分析エラー"""
    pass

class NotionUploadError(FXAnalyzerError):
    """Notion保存エラー"""
    pass

class ConfigurationError(FXAnalyzerError):
    """設定エラー"""
    pass

class NetworkError(FXAnalyzerError):
    """ネットワークエラー"""
    pass

def handle_error(
    exception_type: Type[Exception] = Exception,
    message: str = "",
    reraise: bool = True,
    default_return: Any = None
):
    """エラーハンドリングデコレーター"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                error_msg = message or f"{func.__name__}でエラーが発生しました"
                logger.error(f"{error_msg}: {str(e)}", exc_info=True)
                
                if reraise:
                    raise
                return default_return
                
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exception_type as e:
                error_msg = message or f"{func.__name__}でエラーが発生しました"
                logger.error(f"{error_msg}: {str(e)}", exc_info=True)
                
                if reraise:
                    raise
                return default_return
                
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator

class ErrorRecorder:
    """エラー情報を記録するクラス"""
    
    def __init__(self):
        self.errors = []
        
    def record(self, error: Exception, context: Optional[dict] = None):
        """エラーを記録"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.errors.append(error_info)
        logger.error(f"エラーを記録: {error_info['type']} - {error_info['message']}")
        
    def get_summary(self) -> dict:
        """エラーサマリーを取得"""
        if not self.errors:
            return {"total_errors": 0, "errors": []}
            
        summary = {
            "total_errors": len(self.errors),
            "error_types": {},
            "errors": self.errors[-10:]  # 最新10件
        }
        
        # エラータイプ別の集計
        for error in self.errors:
            error_type = error["type"]
            summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1
            
        return summary
        
    def clear(self):
        """エラーログをクリア"""
        self.errors.clear()

# グローバルエラーレコーダー
error_recorder = ErrorRecorder()

def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """リトライデコレーター"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"{func.__name__}が{max_attempts}回失敗しました")
                        raise
                        
                    logger.warning(
                        f"{func.__name__}が失敗しました（{attempt}/{max_attempts}）。"
                        f"{current_delay}秒後にリトライします: {str(e)}"
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"{func.__name__}が{max_attempts}回失敗しました")
                        raise
                        
                    logger.warning(
                        f"{func.__name__}が失敗しました（{attempt}/{max_attempts}）。"
                        f"{current_delay}秒後にリトライします: {str(e)}"
                    )
                    
                    import time
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator