#!/usr/bin/env python3
"""
Lambda関数にS3アクセス権限を追加するスクリプト
"""
import boto3
import json

def add_s3_permissions(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数のロールにS3権限を追加"""
    lambda_client = boto3.client('lambda', region_name=region)
    iam_client = boto3.client('iam')
    
    try:
        # Lambda関数の設定を取得
        print(f"Lambda関数 '{function_name}' の設定を取得中...")
        function_config = lambda_client.get_function_configuration(FunctionName=function_name)
        role_arn = function_config['Role']
        role_name = role_arn.split('/')[-1]
        
        print(f"IAMロール: {role_name}")
        
        # S3アクセスポリシー
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::fx-analyzer-charts-ecs-prod-455931011903/*",
                        "arn:aws:s3:::fx-analyzer-charts-ecs-prod-455931011903"
                    ]
                }
            ]
        }
        
        # ポリシーを作成または更新
        policy_name = "fx-analyzer-s3-verification-policy"
        
        try:
            # 既存のポリシーを更新
            print(f"ポリシー '{policy_name}' を更新中...")
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(s3_policy)
            )
            print("✅ S3アクセス権限を追加しました")
        except Exception as e:
            print(f"ポリシー更新エラー: {e}")
            
        # 現在のポリシーを確認
        print("\n現在のインラインポリシー:")
        policies = iam_client.list_role_policies(RoleName=role_name)
        for policy in policies['PolicyNames']:
            print(f"  - {policy}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    print("=== Lambda関数S3権限追加スクリプト ===\n")
    
    # AWS認証情報の確認
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}\n")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        return
    
    # S3権限を追加
    if add_s3_permissions():
        print("\n✅ 完了！Lambda関数がS3にアクセスできるようになりました。")
    else:
        print("\n❌ 権限追加に失敗しました。")

if __name__ == "__main__":
    main()