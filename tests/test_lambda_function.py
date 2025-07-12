#!/usr/bin/env python3
"""
Lambda関数のテスト実行スクリプト
"""
import boto3
import json
import time
from datetime import datetime

def test_lambda_function(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数をテスト実行"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    print(f"=== Lambda関数 '{function_name}' のテスト実行 ===\n")
    
    # テストイベント
    test_event = {
        "test": True,
        "time": datetime.now().isoformat()
    }
    
    try:
        print("テスト実行中...")
        print(f"イベント: {json.dumps(test_event, indent=2)}")
        
        # Lambda関数を実行
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # レスポンスを解析
        status_code = response['StatusCode']
        print(f"\nステータスコード: {status_code}")
        
        # ペイロードを読み取り
        payload = response['Payload'].read().decode('utf-8')
        result = json.loads(payload)
        
        if status_code == 200:
            if 'errorMessage' in result:
                print(f"❌ 実行エラー:")
                print(f"   エラーメッセージ: {result['errorMessage']}")
                print(f"   エラータイプ: {result.get('errorType', 'Unknown')}")
                if 'stackTrace' in result:
                    print("\nスタックトレース:")
                    for line in result['stackTrace'][:10]:  # 最初の10行
                        print(f"   {line}")
            else:
                print("✅ 実行成功!")
                print(f"\n結果:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 実行失敗: ステータスコード {status_code}")
            print(f"詳細: {result}")
        
        # CloudWatch Logsの確認方法を表示
        print("\n=== CloudWatch Logsの確認 ===")
        print(f"詳細なログを確認するには:")
        print(f"aws logs tail /aws/lambda/{function_name} --follow --region {region}")
        
        return status_code == 200 and 'errorMessage' not in result
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False

def check_function_configuration(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数の設定を確認"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    print(f"\n=== Lambda関数の設定確認 ===")
    
    try:
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        
        print(f"関数名: {config['FunctionName']}")
        print(f"ランタイム: {config['Runtime']}")
        print(f"ハンドラー: {config['Handler']}")
        print(f"タイムアウト: {config['Timeout']}秒")
        print(f"メモリ: {config['MemorySize']}MB")
        print(f"最終更新: {config['LastModified']}")
        
        # Layerの確認
        layers = config.get('Layers', [])
        if layers:
            print("\nLayers:")
            for layer in layers:
                print(f"  - {layer['Arn']}")
        else:
            print("\nLayers: なし")
        
        # 環境変数の数を確認
        env_vars = config.get('Environment', {}).get('Variables', {})
        print(f"\n環境変数: {len(env_vars)}個設定済み")
        
    except Exception as e:
        print(f"❌ 設定確認エラー: {e}")

def main():
    # AWS認証情報の確認
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}\n")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        return
    
    # 関数の設定確認
    check_function_configuration()
    
    # テスト実行
    print("\n" + "="*50 + "\n")
    if test_lambda_function():
        print("\n✅ テスト完了！Lambda関数は正常に動作しています。")
    else:
        print("\n⚠️  テストでエラーが発生しました。CloudWatch Logsを確認してください。")

if __name__ == "__main__":
    main()