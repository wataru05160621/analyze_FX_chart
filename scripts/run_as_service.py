#!/usr/bin/env python3
"""
システムサービスとして実行するためのスクリプト
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scheduler import FXAnalysisScheduler

def setup_logging():
    """ログ設定"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "service.log"),
            logging.StreamHandler()
        ]
    )

async def run_service():
    """サービスとして実行"""
    logger = logging.getLogger(__name__)
    logger.info("FX分析サービスを開始します")
    
    scheduler = FXAnalysisScheduler()
    scheduler.start()
    
    try:
        # 永続的に実行
        while True:
            await asyncio.sleep(60)
    except Exception as e:
        logger.error(f"サービスエラー: {e}", exc_info=True)
    finally:
        scheduler.stop()
        logger.info("FX分析サービスを停止しました")

if __name__ == "__main__":
    setup_logging()
    
    # 環境変数を読み込む
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
    
    # サービスを実行
    asyncio.run(run_service())