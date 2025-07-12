#!/bin/bash

# FXアナライザー ECS Fargate デプロイスクリプト

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
STACK_NAME="fx-analyzer-ecs"
ENVIRONMENT="${ENVIRONMENT:-prod}"
REGION="${AWS_DEFAULT_REGION:-ap-northeast-1}"
BUCKET_PREFIX="fx-analyzer-ecs-deploy"

log_info "FXアナライザー ECS Fargate デプロイ開始"
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

# Docker確認
if ! command -v docker &> /dev/null; then
    log_error "Dockerがインストールされていません。"
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
    source .env
else
    log_warning ".envファイルが見つかりません"
fi

# 必須パラメータ確認
ALERT_EMAIL="${ALERT_EMAIL:-wataru.s.05160621@gmail.com}"

# CloudFormationテンプレートのデプロイ
log_info "CloudFormationスタックをデプロイ中..."
aws cloudformation deploy \
    --template-file template-ecs.yaml \
    --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
    --capabilities CAPABILITY_IAM \
    --region "${REGION}" \
    --parameter-overrides \
        Environment="${ENVIRONMENT}" \
        AlertEmail="${ALERT_EMAIL}" \
    --s3-bucket "${DEPLOY_BUCKET}"

if [ $? -eq 0 ]; then
    log_success "CloudFormationデプロイ完了!"
else
    log_error "CloudFormationデプロイに失敗しました"
    exit 1
fi

# ECRリポジトリURIを取得
ECR_REPOSITORY_URI=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
    --output text)

log_success "ECRリポジトリURI: ${ECR_REPOSITORY_URI}"

# ECRにログイン
log_info "ECRにログイン中..."
aws ecr get-login-password --region "${REGION}" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Dockerイメージをビルド
log_info "Dockerイメージをビルド中..."
docker build -t fx-analyzer .

# イメージをECRにプッシュ
log_info "Dockerイメージをタグ付け中..."
docker tag fx-analyzer:latest "${ECR_REPOSITORY_URI}:latest"

log_info "DockerイメージをECRにプッシュ中..."
docker push "${ECR_REPOSITORY_URI}:latest"

# タスク定義を更新（新しいイメージURIで）
log_info "ECSタスク定義を更新中..."
aws cloudformation deploy \
    --template-file template-ecs.yaml \
    --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
    --capabilities CAPABILITY_IAM \
    --region "${REGION}" \
    --parameter-overrides \
        Environment="${ENVIRONMENT}" \
        AlertEmail="${ALERT_EMAIL}" \
        ImageUri="${ECR_REPOSITORY_URI}:latest" \
    --s3-bucket "${DEPLOY_BUCKET}"

# Secrets Manager設定
SECRET_NAME="fx-analyzer-ecs-secrets-${ENVIRONMENT}"
log_info "Secrets Managerを設定中..."
aws secretsmanager put-secret-value \
    --secret-id "${SECRET_NAME}" \
    --secret-string "$(cat <<EOF
{
    "OPENAI_API_KEY": "${OPENAI_API_KEY}",
    "CLAUDE_API_KEY": "${CLAUDE_API_KEY}",
    "NOTION_API_KEY": "${NOTION_API_KEY}",
    "NOTION_DATABASE_ID": "${NOTION_DATABASE_ID}",
    "ANALYSIS_MODE": "claude",
    "USE_WEB_CHATGPT": "false"
}
EOF
)" --region "${REGION}"

# ECSクラスターとタスク定義の情報を取得
CLUSTER_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterArn`].OutputValue' \
    --output text)

TASK_DEFINITION_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`TaskDefinitionArn`].OutputValue' \
    --output text)

log_success "=== デプロイ完了! ==="
log_success "ECSクラスター: ${CLUSTER_ARN}"
log_success "タスク定義: ${TASK_DEFINITION_ARN}"
log_success "ECRリポジトリ: ${ECR_REPOSITORY_URI}"

log_info "=== 次のステップ ==="
log_warning "1. SNSサブスクリプションを確認してください:"
echo "受信したメールの確認リンクをクリックしてサブスクリプションを有効化"

log_warning "2. 手動テスト実行:"
echo "aws ecs run-task \\"
echo "    --cluster ${CLUSTER_ARN} \\"
echo "    --task-definition ${TASK_DEFINITION_ARN} \\"
echo "    --launch-type FARGATE \\"
echo "    --network-configuration 'awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}'"

log_warning "3. スケジュール確認:"
echo "EventBridgeルールが設定され、JST 8:00/15:00/21:00に自動実行されます"

log_warning "4. ログ確認:"
echo "aws logs tail /ecs/fx-analyzer-${ENVIRONMENT} --follow"