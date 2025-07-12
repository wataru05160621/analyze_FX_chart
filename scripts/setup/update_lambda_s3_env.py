#!/usr/bin/env python3
"""
Lambda関数にS3環境変数を追加するスクリプト
"""
import boto3
import json

def update_lambda_environment(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数の環境変数を更新"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        print(f"Lambda関数 '{function_name}' の設定を取得中...")
        
        # 現在の設定を取得
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        
        # 既存の環境変数を取得
        env_vars = config.get('Environment', {}).get('Variables', {})
        
        # S3_BUCKET_NAMEを追加
        env_vars['S3_BUCKET_NAME'] = 'fx-analyzer-charts-ecs-prod-455931011903'
        
        print("環境変数を更新中...")
        print(f"  S3_BUCKET_NAME = fx-analyzer-charts-ecs-prod-455931011903")
        
        # 環境変数を更新
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': env_vars
            }
        )
        
        print("✅ 環境変数を更新しました")
        print(f"   最終更新: {response['LastModified']}")
        
        # 更新された環境変数を確認
        print("\n現在の環境変数:")
        updated_vars = response.get('Environment', {}).get('Variables', {})
        for key in sorted(updated_vars.keys()):
            value = updated_vars[key]
            if 'KEY' in key or 'PASSWORD' in key or 'SECRET' in key:
                print(f"   {key}: ***")
            else:
                print(f"   {key}: {value[:50]}..." if len(value) > 50 else f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    print("=== Lambda関数環境変数更新スクリプト ===\n")
    
    # AWS認証情報の確認
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}\n")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        return
    
    # 環境変数を更新
    if update_lambda_environment():
        print("\n✅ 更新完了！")
        print("Lambda関数でS3画像アップロードが使用できるようになりました。")
    else:
        print("\n❌ 更新に失敗しました。")

if __name__ == "__main__":
    main()