#!/usr/bin/env python3
"""
Lambda関数の環境変数を.envファイルから一括更新するスクリプト
"""
import boto3
import os
import json
from pathlib import Path

def load_env_files():
    """環境変数ファイルを読み込み"""
    env_vars = {}
    
    # .envファイルを読み込み
    env_files = ['.env', '.env.phase1']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"読み込み中: {env_file}")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # コメントを除去
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        env_vars[key] = value
    
    return env_vars

def filter_required_env_vars(all_vars):
    """必要な環境変数のみをフィルタリング"""
    required_keys = [
        'CLAUDE_API_KEY',
        'NOTION_API_KEY',
        'NOTION_DATABASE_ID',
        'WORDPRESS_URL',
        'WORDPRESS_USERNAME',
        'WORDPRESS_PASSWORD',
        'WORDPRESS_CATEGORY_USDJPY',
        'WORDPRESS_CATEGORY_ANALYSIS',
        'WORDPRESS_TAG_DAILY_USDJPY',
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET',
        'SLACK_WEBHOOK_URL',
        'ALPHA_VANTAGE_API_KEY',
        'OPENAI_API_KEY',  # 必要に応じて
        'ENABLE_BLOG_POSTING',
        'BLOG_POST_HOUR'
    ]
    
    # AWS予約キーを除外
    reserved_keys = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']
    
    filtered = {}
    for key in required_keys:
        if key in all_vars and key not in reserved_keys:
            filtered[key] = all_vars[key]
    
    return filtered

def update_lambda_environment(function_name='fx-analyzer-prod', region='ap-northeast-1'):
    """Lambda関数の環境変数を更新"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # 現在の設定を取得
        print(f"\nLambda関数 '{function_name}' の現在の設定を取得中...")
        current_config = lambda_client.get_function_configuration(FunctionName=function_name)
        current_env = current_config.get('Environment', {}).get('Variables', {})
        
        print(f"現在の環境変数数: {len(current_env)}")
        
        # .envファイルから環境変数を読み込み
        all_env_vars = load_env_files()
        new_env_vars = filter_required_env_vars(all_env_vars)
        
        # 既存の環境変数とマージ（新しい値で上書き）
        merged_env = current_env.copy()
        merged_env.update(new_env_vars)
        
        print(f"\n更新する環境変数:")
        for key in new_env_vars:
            if key in ['PASSWORD', 'SECRET', 'API_KEY', 'TOKEN']:
                print(f"  {key}: ***")
            else:
                value = new_env_vars[key]
                if len(value) > 50:
                    print(f"  {key}: {value[:20]}...")
                else:
                    print(f"  {key}: {value}")
        
        # 確認
        print(f"\n環境変数を更新しますか？ (y/n): ", end='')
        if input().lower() != 'y':
            print("キャンセルしました")
            return
        
        # 環境変数を更新
        print("\n環境変数を更新中...")
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': merged_env
            }
        )
        
        print("✅ 環境変数の更新完了")
        print(f"   更新後の環境変数数: {len(merged_env)}")
        print(f"   最終更新: {response['LastModified']}")
        
        # 更新後の環境変数を表示
        print("\n設定された環境変数:")
        for key in sorted(merged_env.keys()):
            print(f"  - {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def create_env_json_template():
    """環境変数のJSONテンプレートを作成"""
    all_env_vars = load_env_files()
    required_vars = filter_required_env_vars(all_env_vars)
    
    # JSONファイルに保存
    output_file = 'lambda_env_vars.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(required_vars, f, ensure_ascii=False, indent=2)
    
    print(f"\n環境変数をJSONファイルに保存しました: {output_file}")
    print("このファイルを編集して、update_from_json()関数で適用できます")

def update_from_json(json_file='lambda_env_vars.json', function_name='fx-analyzer-prod', region='ap-northeast-1'):
    """JSONファイルから環境変数を更新"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # JSONファイルを読み込み
        with open(json_file, 'r', encoding='utf-8') as f:
            env_vars = json.load(f)
        
        print(f"JSONファイルから{len(env_vars)}個の環境変数を読み込みました")
        
        # 現在の設定を取得
        current_config = lambda_client.get_function_configuration(FunctionName=function_name)
        current_env = current_config.get('Environment', {}).get('Variables', {})
        
        # マージ
        merged_env = current_env.copy()
        merged_env.update(env_vars)
        
        # 更新
        print("環境変数を更新中...")
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': merged_env
            }
        )
        
        print("✅ 環境変数の更新完了")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    print("=== Lambda環境変数更新スクリプト ===\n")
    
    print("オプションを選択してください:")
    print("1. .envファイルから自動更新")
    print("2. JSONテンプレートを作成")
    print("3. JSONファイルから更新")
    
    choice = input("\n選択 (1/2/3): ")
    
    if choice == '1':
        update_lambda_environment()
    elif choice == '2':
        create_env_json_template()
        print("\nlambda_env_vars.jsonを確認・編集してから、")
        print("python update_lambda_env_vars.py を再実行して選択3を選んでください")
    elif choice == '3':
        update_from_json()
    else:
        print("無効な選択です")

if __name__ == "__main__":
    main()