#!/usr/bin/env python3
"""
現在時刻でFX分析を実行（ブログ投稿設定を一時的に有効化）
"""
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# ブログ投稿を一時的に有効化（時間制限を回避）
os.environ["ENABLE_BLOG_POSTING"] = "true"
# 現在の時刻に関係なく投稿するため、現在の時間を設定
from datetime import datetime
current_hour = datetime.now().hour
os.environ["BLOG_POST_HOUR"] = str(current_hour)

# メイン処理を実行
from src.main import main

if __name__ == "__main__":
    print(f"現在時刻（{datetime.now().strftime('%H:%M')}）でFX分析を実行します...")
    print("ブログ投稿: 有効")
    print()
    
    # 実行
    main()