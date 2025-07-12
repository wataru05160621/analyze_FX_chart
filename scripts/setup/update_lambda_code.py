#!/usr/bin/env python3
"""
既存のLambda関数を検証日数機能付きに更新するスクリプト
"""
import boto3
import zipfile
import os
import json
from pathlib import Path

def create_deployment_package():
    """デプロイメントパッケージを作成"""
    print("デプロイメントパッケージを作成中...")
    
    # 必要なファイルをZIPに追加
    zip_path = "lambda_deployment.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # メインのLambdaハンドラー
        zipf.write("aws_lambda_function.py", "lambda_function.py")
        
        # srcディレクトリの全ファイル
        src_dir = Path("src")
        added_files = set()
        for file_path in src_dir.rglob("*.py"):
            relative_path = file_path.relative_to(src_dir.parent)
            if str(relative_path) not in added_files:
                zipf.write(file_path, str(relative_path))
                added_files.add(str(relative_path))
        
        # docディレクトリ（必要な場合）
        doc_dir = Path("doc/プライスアクションの原則")
        if doc_dir.exists():
            for file_path in doc_dir.rglob("*.md"):
                arcname = f"doc/プライスアクションの原則/{file_path.relative_to(doc_dir)}"
                zipf.write(file_path, arcname)
    
    print(f"✅ デプロイメントパッケージ作成完了: {zip_path}")
    return zip_path

def update_lambda_function(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数を更新"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # デプロイメントパッケージを作成
        zip_path = create_deployment_package()
        
        # ZIPファイルを読み込み
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
        
        print(f"\nLambda関数 '{function_name}' を更新中...")
        
        # 関数コードを更新
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_data
        )
        
        print("✅ Lambda関数のコード更新完了")
        print(f"   最終更新: {response['LastModified']}")
        print(f"   コードサイズ: {response['CodeSize']} bytes")
        
        # 環境変数の確認
        print("\n現在の環境変数を確認中...")
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        
        env_vars = config.get('Environment', {}).get('Variables', {})
        print("設定済み環境変数:")
        for key in env_vars:
            print(f"   - {key}: {'***' if 'KEY' in key or 'PASSWORD' in key else env_vars[key][:20] + '...'}")
        
        # クリーンアップ
        os.remove(zip_path)
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def check_eventbridge_rules(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """EventBridgeルールを確認"""
    events_client = boto3.client('events', region_name=region)
    lambda_client = boto3.client('lambda', region_name=region)
    
    print("\nEventBridgeルールを確認中...")
    
    try:
        # Lambda関数のARNを取得
        func_config = lambda_client.get_function_configuration(FunctionName=function_name)
        function_arn = func_config['FunctionArn']
        
        # すべてのルールを取得
        rules = events_client.list_rules()
        
        related_rules = []
        for rule in rules['Rules']:
            # ターゲットを確認
            targets = events_client.list_targets_by_rule(Rule=rule['Name'])
            for target in targets['Targets']:
                if function_arn in target.get('Arn', ''):
                    related_rules.append(rule)
                    break
        
        if related_rules:
            print("✅ 関連するEventBridgeルール:")
            for rule in related_rules:
                print(f"   - {rule['Name']}: {rule.get('ScheduleExpression', 'N/A')}")
                print(f"     状態: {rule['State']}")
        else:
            print("⚠️  EventBridgeルールが見つかりません")
            print("   スケジュール実行が設定されていない可能性があります")
        
    except Exception as e:
        print(f"❌ EventBridge確認エラー: {e}")

def main():
    print("=== Lambda関数更新スクリプト ===\n")
    
    # AWS認証情報の確認
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}\n")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        return
    
    # Lambda関数の更新
    if update_lambda_function():
        # EventBridgeルールの確認
        check_eventbridge_rules()
        
        print("\n✅ 更新完了！")
        print("\n次のステップ:")
        print("1. AWS ConsoleでLambda関数をテスト実行")
        print("2. CloudWatch Logsで実行ログを確認")
        print("3. 必要に応じて環境変数を追加")
    else:
        print("\n❌ 更新に失敗しました")

if __name__ == "__main__":
    main()