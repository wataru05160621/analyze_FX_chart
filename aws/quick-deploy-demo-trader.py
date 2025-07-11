#!/usr/bin/env python3
"""
Phase1 デモトレーダー クイックデプロイスクリプト
"""
import os
import sys
import subprocess
import json
import time
from pathlib import Path

def run_command(cmd, check=True):
    """コマンド実行"""
    print(f"実行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"エラー: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def load_env_file(env_file='.env'):
    """環境変数ファイルを読み込み"""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 環境変数に設定されていない場合のみセット
                    if key not in os.environ:
                        os.environ[key] = value

def main():
    print("=== Phase1 デモトレーダー クイックデプロイ ===")
    
    # .envファイルを読み込み
    load_env_file('.env')
    load_env_file('.env.phase1')
    
    # 環境変数チェック
    required_env = {
        'ALPHA_VANTAGE_API_KEY': os.environ.get('ALPHA_VANTAGE_API_KEY'),
        'CLAUDE_API_KEY': os.environ.get('CLAUDE_API_KEY')
    }
    
    for key, value in required_env.items():
        if not value:
            print(f"エラー: {key} が設定されていません")
            print(f"実行: export {key}=your_key")
            sys.exit(1)
    
    # AWS設定
    region = os.environ.get('AWS_REGION', 'ap-northeast-1')
    account_id = run_command("aws sts get-caller-identity --query Account --output text")
    
    print(f"AWSアカウント: {account_id}")
    print(f"リージョン: {region}")
    
    # 1. ECRリポジトリ
    print("\n1. ECRリポジトリ設定...")
    repo_name = "phase1-demo-trader"
    
    # リポジトリ存在確認
    check_repo = subprocess.run(
        f"aws ecr describe-repositories --repository-names {repo_name} --region {region}",
        shell=True, capture_output=True
    )
    
    if check_repo.returncode != 0:
        run_command(f"aws ecr create-repository --repository-name {repo_name} --region {region}")
        print("ECRリポジトリ作成完了")
    else:
        print("ECRリポジトリは既に存在")
    
    # 2. Dockerイメージ
    print("\n2. Dockerイメージのビルドとプッシュ...")
    
    # ECRログイン
    login_cmd = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
    run_command(login_cmd)
    
    # ビルド
    run_command("docker build -f aws/Dockerfile.demo-trader -t phase1-demo-trader .")
    
    # タグ付けとプッシュ
    image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repo_name}:latest"
    run_command(f"docker tag phase1-demo-trader:latest {image_uri}")
    run_command(f"docker push {image_uri}")
    
    print(f"イメージURI: {image_uri}")
    
    # 3. ネットワーク情報取得
    print("\n3. ネットワーク情報取得...")
    vpc_id = run_command("aws ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text")
    subnets = run_command("aws ec2 describe-subnets --filters Name=vpc-id,Values=" + vpc_id + " --query 'Subnets[*].SubnetId' --output text")
    subnet_list = subnets.replace('\t', ',')
    
    # 4. CloudFormationデプロイ
    print("\n4. CloudFormationスタックデプロイ...")
    
    # パラメータ作成
    params = [
        {"ParameterKey": "ImageUri", "ParameterValue": image_uri},
        {"ParameterKey": "VpcId", "ParameterValue": vpc_id},
        {"ParameterKey": "SubnetIds", "ParameterValue": subnet_list},
        {"ParameterKey": "AlphaVantageApiKey", "ParameterValue": required_env['ALPHA_VANTAGE_API_KEY']},
        {"ParameterKey": "ClaudeApiKey", "ParameterValue": required_env['CLAUDE_API_KEY']},
        {"ParameterKey": "SlackWebhookUrl", "ParameterValue": os.environ.get('SLACK_WEBHOOK_URL', '')},
        {"ParameterKey": "NotificationEmail", "ParameterValue": os.environ.get('NOTIFICATION_EMAIL', '')}
    ]
    
    params_file = Path("demo-trader-params.json")
    with open(params_file, 'w') as f:
        json.dump(params, f, indent=2)
    
    stack_name = "phase1-demo-trader"
    
    # スタック存在確認
    check_stack = subprocess.run(
        f"aws cloudformation describe-stacks --stack-name {stack_name} --region {region}",
        shell=True, capture_output=True
    )
    
    if check_stack.returncode == 0:
        print("既存スタックを更新...")
        run_command(f"""
            aws cloudformation update-stack \
                --stack-name {stack_name} \
                --template-body file://aws/cloudformation-demo-trader.yaml \
                --parameters file://demo-trader-params.json \
                --capabilities CAPABILITY_IAM \
                --region {region}
        """)
        
        print("スタック更新完了を待機...")
        run_command(f"aws cloudformation wait stack-update-complete --stack-name {stack_name} --region {region}")
    else:
        print("新規スタックを作成...")
        run_command(f"""
            aws cloudformation create-stack \
                --stack-name {stack_name} \
                --template-body file://aws/cloudformation-demo-trader.yaml \
                --parameters file://demo-trader-params.json \
                --capabilities CAPABILITY_IAM \
                --region {region}
        """)
        
        print("スタック作成完了を待機...")
        run_command(f"aws cloudformation wait stack-create-complete --stack-name {stack_name} --region {region}")
    
    # クリーンアップ
    params_file.unlink()
    
    # 5. 結果確認
    print("\n5. デプロイ結果確認...")
    
    # スタック出力
    outputs = run_command(f"aws cloudformation describe-stacks --stack-name {stack_name} --query 'Stacks[0].Outputs' --region {region}")
    outputs_json = json.loads(outputs)
    
    print("\n=== スタック出力 ===")
    for output in outputs_json:
        print(f"{output['OutputKey']}: {output['OutputValue']}")
    
    # ECSサービス状態
    cluster_name = next(o['OutputValue'] for o in outputs_json if o['OutputKey'] == 'ECSClusterName')
    service_name = next(o['OutputValue'] for o in outputs_json if o['OutputKey'] == 'ServiceName')
    
    service_status = run_command(f"""
        aws ecs describe-services \
            --cluster {cluster_name} \
            --services {service_name} \
            --query 'services[0].{{Status:status,Running:runningCount,Desired:desiredCount}}' \
            --region {region}
    """)
    
    print("\n=== ECSサービス状態 ===")
    print(service_status)
    
    # ログ確認
    print("\n=== 最新ログ ===")
    try:
        logs = run_command(f"aws logs tail /ecs/phase1-demo-trader --since 1m --region {region}", check=False)
        if logs:
            print(logs)
        else:
            print("まだログがありません")
    except:
        print("ログ取得エラー")
    
    print("\n✅ デプロイ完了！")
    print(f"\n📊 ログ監視: aws logs tail /ecs/phase1-demo-trader --follow --region {region}")
    print(f"📈 トレード確認: aws dynamodb scan --table-name phase1-trades --region {region}")
    print(f"🔄 サービス再起動: aws ecs update-service --cluster {cluster_name} --service {service_name} --force-new-deployment --region {region}")

if __name__ == "__main__":
    main()