#!/bin/bash
# AWS Lambda デプロイスクリプト

set -e

# 色付きメッセージ用の関数
print_success() { echo -e "\033[32m✅ $1\033[0m"; }
print_error() { echo -e "\033[31m❌ $1\033[0m"; }
print_info() { echo -e "\033[34mℹ️ $1\033[0m"; }
print_warning() { echo -e "\033[33m⚠️ $1\033[0m"; }

# パラメータの設定
ENVIRONMENT=${1:-dev}
DEPLOY_METHOD=${2:-sam}  # sam または serverless

print_info "🚀 AWS Lambda デプロイを開始します"
print_info "Environment: $ENVIRONMENT"
print_info "Deploy Method: $DEPLOY_METHOD"

# 必要な環境変数のチェック
check_env_vars() {
    local required_vars=(
        "OPENAI_API_KEY"
        "NOTION_API_KEY"
        "NOTION_DATABASE_ID"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "必要な環境変数が設定されていません:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        print_info "以下のコマンドで環境変数を設定してください:"
        echo "export OPENAI_API_KEY=your_key_here"
        echo "export NOTION_API_KEY=your_key_here"
        echo "export NOTION_DATABASE_ID=your_id_here"
        exit 1
    fi
}

# AWS CLIの確認
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLIがインストールされていません"
        print_info "以下のコマンドでインストールしてください:"
        print_info "curl 'https://awscli.amazonaws.com/AWSCLIV2.pkg' -o 'AWSCLIV2.pkg'"
        print_info "sudo installer -pkg AWSCLIV2.pkg -target /"
        exit 1
    fi
    
    # AWS認証情報の確認
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS認証情報が設定されていません"
        print_info "以下のコマンドで設定してください:"
        print_info "aws configure"
        exit 1
    fi
    
    print_success "AWS CLI設定OK"
}

# SAMでのデプロイ
deploy_with_sam() {
    print_info "SAM (Serverless Application Model) でデプロイします"
    
    # SAM CLIの確認
    if ! command -v sam &> /dev/null; then
        print_error "SAM CLIがインストールされていません"
        print_info "以下のコマンドでインストールしてください:"
        print_info "brew install aws/tap/aws-sam-cli"
        exit 1
    fi
    
    # S3バケット名を生成
    S3_BUCKET="fx-analyzer-images-${ENVIRONMENT}"
    
    print_info "SAMアプリケーションをビルド中..."
    sam build --use-container
    
    print_info "SAMアプリケーションをデプロイ中..."
    sam deploy \
        --stack-name "fx-analyzer-${ENVIRONMENT}" \
        --s3-bucket "fx-analyzer-deploy-${ENVIRONMENT}" \
        --s3-prefix "fx-analyzer" \
        --region ap-northeast-1 \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            OpenAIAPIKey="$OPENAI_API_KEY" \
            NotionAPIKey="$NOTION_API_KEY" \
            NotionDatabaseId="$NOTION_DATABASE_ID" \
            S3BucketName="$S3_BUCKET" \
            TradingViewURL="${TRADINGVIEW_CUSTOM_URL:-https://jp.tradingview.com/chart/}" \
        --confirm-changeset
        
    print_success "SAMデプロイ完了"
}

# Serverless Frameworkでのデプロイ
deploy_with_serverless() {
    print_info "Serverless Framework でデプロイします"
    
    # Serverless CLIの確認
    if ! command -v serverless &> /dev/null; then
        print_error "Serverless CLIがインストールされていません"
        print_info "以下のコマンドでインストールしてください:"
        print_info "npm install -g serverless"
        exit 1
    fi
    
    # プラグインのインストール
    if [[ ! -d "node_modules" ]]; then
        print_info "Node.js依存関係をインストール中..."
        npm install
    fi
    
    print_info "Serverless アプリケーションをデプロイ中..."
    serverless deploy --stage "$ENVIRONMENT" --region ap-northeast-1
    
    print_success "Serverlessデプロイ完了"
}

# テスト実行
test_lambda() {
    print_info "Lambda関数をテスト中..."
    
    if [[ "$DEPLOY_METHOD" == "sam" ]]; then
        # SAMローカルテスト
        sam local invoke TestFunction --event test-event.json
    else
        # Serverless invoke
        serverless invoke --function test --stage "$ENVIRONMENT"
    fi
}

# メイン処理
main() {
    print_info "デプロイ前チェックを実行中..."
    
    # 環境変数チェック
    check_env_vars
    
    # AWS CLIチェック
    check_aws_cli
    
    # .envファイルから環境変数を読み込み
    if [[ -f ".env" ]]; then
        print_info ".envファイルから環境変数を読み込み中..."
        set -a
        source .env
        set +a
    fi
    
    # デプロイ方法に応じた処理
    case "$DEPLOY_METHOD" in
        "sam")
            deploy_with_sam
            ;;
        "serverless")
            deploy_with_serverless
            ;;
        *)
            print_error "無効なデプロイ方法: $DEPLOY_METHOD"
            print_info "使用方法: $0 [environment] [sam|serverless]"
            exit 1
            ;;
    esac
    
    print_success "🎉 デプロイが完了しました！"
    
    # デプロイ後の情報表示
    print_info "📋 デプロイ情報:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Method: $DEPLOY_METHOD"
    echo "  Region: ap-northeast-1"
    echo "  Function Name: fx-analyzer-$ENVIRONMENT"
    
    print_info "🔧 テスト実行:"
    echo "  aws lambda invoke --function-name fx-analyzer-test-$ENVIRONMENT response.json"
    
    print_info "📊 ログ確認:"
    echo "  aws logs tail /aws/lambda/fx-analyzer-$ENVIRONMENT --follow"
}

# スクリプト実行
main "$@"