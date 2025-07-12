#!/usr/bin/env python3
"""
S3Uploaderのテストスクリプト
"""
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

# 環境変数を設定
os.environ['S3_BUCKET_NAME'] = 'fx-analyzer-charts-ecs-prod-455931011903'

# S3Uploaderをテスト
from src.image_uploader import get_uploader, S3Uploader

print("=== S3Uploaderテスト ===\n")

# 環境変数の確認
print(f"S3_BUCKET_NAME: {os.getenv('S3_BUCKET_NAME')}")

# アップローダーを取得
uploader = get_uploader()
print(f"\nアップローダータイプ: {type(uploader).__name__ if uploader else 'None'}")

if uploader and isinstance(uploader, S3Uploader):
    # テスト画像を探す
    test_image = None
    for path in Path("screenshots").rglob("*.png"):
        test_image = path
        break
    
    if test_image:
        print(f"\nテスト画像: {test_image}")
        print("アップロード中...")
        
        try:
            url = uploader.upload(test_image)
            if url:
                print(f"\n✅ アップロード成功!")
                print(f"署名付きURL: {url[:100]}...")
            else:
                print(f"\n❌ アップロード失敗")
        except Exception as e:
            print(f"\n❌ エラー: {e}")
    else:
        print("\nテスト画像が見つかりません")
else:
    print("\nS3Uploaderが取得できませんでした")