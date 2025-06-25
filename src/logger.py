"""
ロギング設定モジュール
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

from .config import LOG_DIR, LOG_FILE

class CustomFormatter(logging.Formatter):
    """カスタムログフォーマッター"""
    
    def format(self, record):
        # エラーレベルに応じて絵文字を追加
        emoji_map = {
            logging.DEBUG: "🔍",
            logging.INFO: "ℹ️",
            logging.WARNING: "⚠️",
            logging.ERROR: "❌",
            logging.CRITICAL: "🚨"
        }
        
        record.emoji = emoji_map.get(record.levelno, "")
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """JSON形式のログフォーマッター"""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj, ensure_ascii=False)

def setup_logger(
    name: str = "fx_analyzer",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    use_json: bool = False
) -> logging.Logger:
    """ロガーをセットアップ"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ログフォーマット
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = CustomFormatter(
            '%(asctime)s - %(emoji)s %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー
    if log_file is None:
        log_file = LOG_FILE
        
    LOG_DIR.mkdir(exist_ok=True)
    
    # ローテーティングファイルハンドラー（10MB、5世代）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # エラー専用ファイルハンドラー
    error_file = LOG_DIR / f"{name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

# グローバルロガーのセットアップ
logger = setup_logger()

def log_function_call(func):
    """関数呼び出しをログするデコレーター"""
    def wrapper(*args, **kwargs):
        logger.debug(f"関数 {func.__name__} を呼び出し: args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"関数 {func.__name__} が正常終了")
            return result
        except Exception as e:
            logger.error(f"関数 {func.__name__} でエラー発生: {e}", exc_info=True)
            raise
    return wrapper