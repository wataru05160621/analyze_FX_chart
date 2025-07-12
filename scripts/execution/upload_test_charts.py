#!/usr/bin/env python3
"""
テスト用チャート画像をS3にアップロードするスクリプト
"""
import boto3
import os
from datetime import datetime
from pathlib import Path

def upload_test_charts():
    """ローカルのチャート画像をS3にアップロード"""
    s3_client = boto3.client('s3')
    bucket_name = 'fx-analyzer-charts-ecs-prod-455931011903'
    
    # USD_JPYディレクトリからチャート画像を探す
    screenshots_dir = Path("screenshots/USD_JPY")
    if not screenshots_dir.exists():
        print(f"❌ USD_JPYディレクトリが見つかりません")
        return
    
    # チャート画像を探す
    chart_files = list(screenshots_dir.glob("*.png"))
    if not chart_files:
        print(f"❌ チャート画像が見つかりません")
        return
    
    # 最新の4つのファイルを取得（5min, 1hour）
    chart_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    timeframes = ['5min', '1hour']
    
    # 4hourと1dayは1hourのチャートをコピーして使用
    latest_1hour = None
    for chart_file in chart_files:
        if '1hour' in chart_file.name:
            latest_1hour = chart_file
            break
    
    uploaded_count = 0
    for timeframe in timeframes:
        # 対応するファイルを探す
        for chart_file in chart_files:
            if timeframe in chart_file.name:
                # S3キーを作成
                today = datetime.now().strftime('%Y-%m-%d')
                s3_key = f"charts/USDJPY/{today}/{timeframe}_{datetime.now().strftime('%H%M%S')}.png"
                
                try:
                    # S3にアップロード
                    print(f"アップロード中: {chart_file.name} → s3://{bucket_name}/{s3_key}")
                    s3_client.upload_file(
                        str(chart_file),
                        bucket_name,
                        s3_key,
                        ExtraArgs={'ContentType': 'image/png'}
                    )
                    uploaded_count += 1
                    print(f"✅ アップロード完了")
                    break
                except Exception as e:
                    print(f"❌ アップロードエラー: {e}")
    
    # 4hourと1dayのチャートもアップロード（1hourのチャートを使用）
    if latest_1hour:
        for timeframe in ['4hour', '1day']:
            today = datetime.now().strftime('%Y-%m-%d')
            s3_key = f"charts/USDJPY/{today}/{timeframe}_{datetime.now().strftime('%H%M%S')}.png"
            
            try:
                print(f"アップロード中: {latest_1hour.name} → s3://{bucket_name}/{s3_key} (代替)")
                s3_client.upload_file(
                    str(latest_1hour),
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': 'image/png'}
                )
                uploaded_count += 1
                print(f"✅ アップロード完了")
            except Exception as e:
                print(f"❌ アップロードエラー: {e}")
    
    print(f"\n合計 {uploaded_count} 個のチャート画像をアップロードしました")
    
    # アップロードしたファイルを確認
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=f"charts/USDJPY/",
            MaxKeys=10
        )
        
        if 'Contents' in response:
            print("\n最新のチャート画像:")
            for obj in sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[:5]:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
    except Exception as e:
        print(f"❌ 一覧取得エラー: {e}")

def main():
    print("=== テストチャートS3アップロードスクリプト ===\n")
    
    # AWS認証情報の確認
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}\n")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        return
    
    upload_test_charts()

if __name__ == "__main__":
    main()