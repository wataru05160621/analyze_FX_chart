#!/usr/bin/env python3
"""
FX分析スケジューラーの起動スクリプト
"""
import asyncio
import logging
from src.scheduler import main

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # スケジューラーを実行
    asyncio.run(main())