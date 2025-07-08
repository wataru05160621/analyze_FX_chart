#!/bin/bash

# FXアナライザー ECS更新スクリプト（マルチ通貨対応）

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

log_info "FXアナライザー ECS更新開始（マルチ通貨対応）"
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

# Dockerイメージをビルド（マルチ通貨対応）
log_info "Dockerイメージをビルド中（マルチ通貨対応版）..."
docker build -t fx-analyzer-multi .

# イメージをECRにプッシュ
log_info "Dockerイメージをタグ付け中..."
docker tag fx-analyzer-multi:latest "${ECR_REPOSITORY_URI}:latest"
docker tag fx-analyzer-multi:latest "${ECR_REPOSITORY_URI}:multi-currency-$(date +%Y%m%d-%H%M%S)"

log_info "DockerイメージをECRにプッシュ中..."
docker push "${ECR_REPOSITORY_URI}:latest"
docker push "${ECR_REPOSITORY_URI}:multi-currency-$(date +%Y%m%d-%H%M%S)"

# ECSサービスを強制更新
CLUSTER_NAME="fx-analyzer-cluster-${ENVIRONMENT}"
log_info "ECSタスクを更新中..."

# タスク定義を強制的に新しいリビジョンで更新
aws ecs update-service \
    --cluster "${CLUSTER_NAME}" \
    --service "fx-analyzer-service-${ENVIRONMENT}" \
    --force-new-deployment \
    --region "${REGION}" 2>/dev/null || true

# スケジュールタスクのタスク定義を更新
log_info "EventBridgeのターゲットを更新中..."

# タスク定義ARNを取得
TASK_DEFINITION_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-${ENVIRONMENT}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`TaskDefinitionArn`].OutputValue' \
    --output text)

# 各EventBridgeルールのターゲットを更新
for RULE_NAME in "fx-analyzer-ecs-morning-${ENVIRONMENT}" "fx-analyzer-ecs-afternoon-${ENVIRONMENT}" "fx-analyzer-ecs-evening-${ENVIRONMENT}"; do
    log_info "ルール ${RULE_NAME} を更新中..."
    
    # 既存のターゲットを取得
    TARGETS=$(aws events list-targets-by-rule --rule "${RULE_NAME}" --region "${REGION}")
    
    if [ ! -z "$TARGETS" ]; then
        # ターゲットを更新（新しいタスク定義を使用）
        aws events put-targets \
            --rule "${RULE_NAME}" \
            --targets "$(echo $TARGETS | jq --arg arn "${TASK_DEFINITION_ARN}:LATEST" '.Targets[0].EcsParameters.TaskDefinitionArn = $arn | .Targets')" \
            --region "${REGION}"
    fi
done

log_success "=== 更新完了! ==="
log_success "マルチ通貨対応版がデプロイされました"

log_info "=== 次のステップ ==="
log_warning "1. ログを確認:"
echo "aws logs tail /ecs/fx-analyzer-${ENVIRONMENT} --follow"

log_warning "2. 手動テスト実行（AM8:00モード）:"
echo "aws ecs run-task \\"
echo "    --cluster ${CLUSTER_NAME} \\"
echo "    --task-definition ${TASK_DEFINITION_ARN}:LATEST \\"
echo "    --launch-type FARGATE \\"
echo "    --network-configuration 'awsvpcConfiguration={subnets=[$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=fx-analyzer-public-subnet-*-${ENVIRONMENT}" --query "Subnets[0].SubnetId" --output text)],securityGroups=[$(aws ec2 describe-security-groups --filters "Name=group-name,Values=fx-analyzer-ecs-sg-${ENVIRONMENT}" --query "SecurityGroups[0].GroupId" --output text)],assignPublicIp=ENABLED}' \\"
echo "    --overrides '{\"containerOverrides\":[{\"name\":\"fx-analyzer\",\"environment\":[{\"name\":\"FORCE_HOUR\",\"value\":\"8\"}]}]}'"

log_warning "3. 定期実行スケジュール:"
echo "- 朝 8:00 JST: USD/JPY, BTC/USD, XAU/USD分析 + USD/JPYブログ投稿"
echo "- 昼 15:00 JST: USD/JPY分析のみ"
echo "- 夜 21:00 JST: USD/JPY分析のみ"