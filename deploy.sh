#!/bin/bash

# FXアナライザー AWS Lambda デプロイスクリプト

set -e  # エラーで停止

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 設定
STACK_NAME="fx-analyzer"
ENVIRONMENT="${ENVIRONMENT:-prod}"
REGION="${AWS_DEFAULT_REGION:-ap-northeast-1}"
BUCKET_PREFIX="fx-analyzer-deploy"

log_info "FXアナライザー AWS Lambda デプロイ開始"
log_info "スタック名: ${STACK_NAME}-${ENVIRONMENT}"
log_info "リージョン: ${REGION}"

# AWS CLI設定確認
log_info "AWS CLI設定確認中..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS CLIが設定されていません。aws configure を実行してください。"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_success "AWS認証済み (Account: ${ACCOUNT_ID})"

# SAM CLI確認
if ! command -v sam &> /dev/null; then
    log_error "SAM CLIがインストールされていません。"
    log_info "インストール方法: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# デプロイバケット名
DEPLOY_BUCKET="${BUCKET_PREFIX}-${ACCOUNT_ID}-${REGION}"

# S3バケット作成（存在しない場合）
log_info "デプロイ用S3バケット確認中..."
if ! aws s3 ls "s3://${DEPLOY_BUCKET}" > /dev/null 2>&1; then
    log_info "S3バケット作成中: ${DEPLOY_BUCKET}"
    aws s3 mb "s3://${DEPLOY_BUCKET}" --region "${REGION}"
else
    log_success "S3バケット存在確認: ${DEPLOY_BUCKET}"
fi

# 環境変数確認
log_info "環境変数確認中..."
if [ -f .env ]; then
    log_success ".envファイルが見つかりました"
    # .envからAPIキーを読み込み
    source .env
else
    log_warning ".envファイルが見つかりません"
fi

# 必須パラメータ確認
ALERT_EMAIL="${ALERT_EMAIL:-your-email@example.com}"
if [ "$ALERT_EMAIL" = "your-email@example.com" ]; then
    read -p "アラート通知用メールアドレスを入力してください: " ALERT_EMAIL
fi

# SAMビルド
log_info "SAMビルド開始..."
sam build

# SAMデプロイ
log_info "SAMデプロイ開始..."
sam deploy \
    --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
    --s3-bucket "${DEPLOY_BUCKET}" \
    --capabilities CAPABILITY_IAM \
    --region "${REGION}" \
    --parameter-overrides \
        Environment="${ENVIRONMENT}" \
        AlertEmail="${ALERT_EMAIL}" \
    --confirm-changeset

if [ $? -eq 0 ]; then
    log_success "デプロイ完了!"
    
    # スタック情報表示
    log_info "スタック情報取得中..."
    FUNCTION_ARN=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
        --region "${REGION}" \
        --query 'Stacks[0].Outputs[?OutputKey==`FXAnalyzerFunction`].OutputValue' \
        --output text)
    
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
        --region "${REGION}" \
        --query 'Stacks[0].Outputs[?OutputKey==`ChartStorageBucket`].OutputValue' \
        --output text 2>/dev/null || echo "未作成")
    
    log_success "Lambda関数ARN: ${FUNCTION_ARN}"
    log_success "S3バケット: ${BUCKET_NAME}"
    
    # Secrets Manager設定案内
    SECRET_NAME="fx-analyzer-secrets-${ENVIRONMENT}"
    log_info "=== 次のステップ ==="
    log_warning "1. Secrets Managerでシークレットを更新してください:"
    echo "aws secretsmanager put-secret-value \\"
    echo "    --secret-id ${SECRET_NAME} \\"
    echo "    --secret-string '{"
    echo "        \"OPENAI_API_KEY\": \"${OPENAI_API_KEY:-your-openai-key}\","
    echo "        \"CLAUDE_API_KEY\": \"${CLAUDE_API_KEY:-your-claude-key}\","
    echo "        \"NOTION_API_KEY\": \"${NOTION_API_KEY:-your-notion-key}\","
    echo "        \"NOTION_DATABASE_ID\": \"${NOTION_DATABASE_ID:-your-notion-database-id}\","
    echo "        \"ANALYSIS_MODE\": \"claude\","
    echo "        \"USE_WEB_CHATGPT\": \"false\""
    echo "    }'"
    
    log_warning "2. SNSサブスクリプションを確認してください:"
    echo "受信したメールの確認リンクをクリックしてサブスクリプションを有効化"
    
    log_warning "3. テスト実行:"
    echo "aws lambda invoke --function-name fx-analyzer-${ENVIRONMENT} --payload '{}' response.json"
    
else
    log_error "デプロイに失敗しました"
    exit 1
fi

