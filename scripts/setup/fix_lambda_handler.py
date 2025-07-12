#!/usr/bin/env python3
"""
Lambda関数のハンドラー設定を修正するスクリプト
"""
import boto3
import json

def update_lambda_handler(function_name='fx-analyzer-prod', region='ap-northeast-1'):
    """Lambda関数のハンドラーを正しく設定"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        print(f"Lambda関数 '{function_name}' のハンドラー設定を更新中...")
        
        # 現在の設定を確認
        current_config = lambda_client.get_function_configuration(FunctionName=function_name)
        print(f"現在のハンドラー: {current_config.get('Handler')}")
        
        # ハンドラーを更新
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler='lambda_function.lambda_handler',  # 正しいハンドラー名
            Timeout=600,  # 10分
            MemorySize=1024  # 1GB
        )
        
        print("✅ ハンドラー設定を更新しました")
        print(f"   新しいハンドラー: {response['Handler']}")
        print(f"   タイムアウト: {response['Timeout']}秒")
        print(f"   メモリ: {response['MemorySize']}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_lambda_again(function_name='fx-analyzer-prod', region='ap-northeast-1'):
    """修正後のLambda関数をテスト"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    print(f"\n=== Lambda関数の再テスト ===")
    
    try:
        # テストイベント
        test_event = {
            'test': True,
            'source': 'manual-test'
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"ステータスコード: {status_code}")
        
        if status_code == 200 and 'errorMessage' not in payload:
            print("✅ テスト実行成功")
            print(f"レスポンス: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        else:
            print("❌ テスト実行でエラーが発生")
            if 'errorMessage' in payload:
                print(f"エラー: {payload['errorMessage']}")
                print(f"エラータイプ: {payload.get('errorType', 'Unknown')}")
            else:
                print(f"レスポンス: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            # CloudWatch Logsの確認方法を案内
            print("\n詳細なエラーログを確認するには:")
            print(f"aws logs tail /aws/lambda/{function_name} --follow --region {region}")
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")

def check_s3_bucket(region='ap-northeast-1'):
    """S3バケットの確認と検証開始日の設定"""
    s3_client = boto3.client('s3', region_name=region)
    
    print("\n=== S3バケットの確認 ===")
    
    try:
        # バケット一覧
        buckets = s3_client.list_buckets()
        fx_buckets = [b['Name'] for b in buckets['Buckets'] if 'fx' in b['Name'].lower()]
        
        if fx_buckets:
            print("FX関連のS3バケット:")
            for bucket in fx_buckets:
                print(f"  - {bucket}")
            
            # 最初のバケットに検証開始日を設定
            bucket_name = fx_buckets[0]
            print(f"\n検証開始日を設定しますか？ (バケット: {bucket_name}) (y/n): ", end='')
            
            if input().lower() == 'y':
                import json
                from datetime import datetime
                
                start_date_data = {
                    "start_date": datetime.utcnow().isoformat(),
                    "phase": "Phase1",
                    "description": "FXスキャルピング検証プロジェクト"
                }
                
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key='phase1_start_date.json',
                    Body=json.dumps(start_date_data, ensure_ascii=False, indent=2),
                    ContentType='application/json'
                )
                
                print("✅ 検証開始日を設定しました")
        else:
            print("FX関連のS3バケットが見つかりません")
            
    except Exception as e:
        print(f"❌ S3エラー: {e}")

def main():
    print("=== Lambda関数の修正 ===\n")
    
    # ハンドラー設定を修正
    if update_lambda_handler():
        # 少し待機（設定反映のため）
        import time
        print("\n設定反映のため3秒待機中...")
        time.sleep(3)
        
        # 再テスト
        test_lambda_again()
        
        # S3バケット確認
        check_s3_bucket()
        
        print("\n=== 完了 ===")
        print("\n次のステップ:")
        print("1. AWS ConsoleでCloudWatch Logsを確認")
        print("2. エラーがある場合は、ログの詳細を確認")
        print("3. 明日の朝8時に自動実行されます")
    else:
        print("\nハンドラー設定の更新に失敗しました")

if __name__ == "__main__":
    main()