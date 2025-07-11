#!/bin/bash

# Phase1 デモトレーダー デプロイスクリプト
set -e

echo "=== Phase1 Demo Trader Deployment Script ==="

# 設定
REGION=${AWS_REGION:-ap-northeast-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
STACK_NAME="phase1-demo-trader"
REPOSITORY_NAME="phase1-demo-trader"

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}AWS Account ID: ${ACCOUNT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"

# 1. ECRリポジトリの作成または確認
echo -e "\n${GREEN}1. Setting up ECR repository...${NC}"
if aws ecr describe-repositories --repository-names ${REPOSITORY_NAME} --region ${REGION} 2>/dev/null; then
    echo "ECR repository already exists"
else
    aws ecr create-repository --repository-name ${REPOSITORY_NAME} --region ${REGION}
    echo "ECR repository created"
fi

# 2. Dockerイメージのビルドとプッシュ
echo -e "\n${GREEN}2. Building and pushing Docker image...${NC}"

# ECRログイン
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# イメージビルド
docker build -f aws/Dockerfile.demo-trader -t ${REPOSITORY_NAME} .

# タグ付けとプッシュ
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:latest"
docker tag ${REPOSITORY_NAME}:latest ${IMAGE_URI}
docker push ${IMAGE_URI}

echo -e "${GREEN}Docker image pushed: ${IMAGE_URI}${NC}"

# 3. パラメータの設定
echo -e "\n${GREEN}3. Setting up CloudFormation parameters...${NC}"

# VPCとサブネットの取得
DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text)
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${DEFAULT_VPC}" --query "Subnets[*].SubnetId" --output text | tr '\t' ',')

# 環境変数の確認
if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    echo -e "${RED}Error: ALPHA_VANTAGE_API_KEY is not set${NC}"
    echo "Please set: export ALPHA_VANTAGE_API_KEY=your_key"
    exit 1
fi

if [ -z "$CLAUDE_API_KEY" ]; then
    echo -e "${RED}Error: CLAUDE_API_KEY is not set${NC}"
    echo "Please set: export CLAUDE_API_KEY=your_key"
    exit 1
fi

# パラメータファイルの作成
cat > demo-trader-params.json << EOF
[
  {
    "ParameterKey": "ImageUri",
    "ParameterValue": "${IMAGE_URI}"
  },
  {
    "ParameterKey": "VpcId",
    "ParameterValue": "${DEFAULT_VPC}"
  },
  {
    "ParameterKey": "SubnetIds",
    "ParameterValue": "${SUBNETS}"
  },
  {
    "ParameterKey": "AlphaVantageApiKey",
    "ParameterValue": "${ALPHA_VANTAGE_API_KEY}"
  },
  {
    "ParameterKey": "ClaudeApiKey",
    "ParameterValue": "${CLAUDE_API_KEY}"
  },
  {
    "ParameterKey": "SlackWebhookUrl",
    "ParameterValue": "${SLACK_WEBHOOK_URL:-}"
  },
  {
    "ParameterKey": "NotificationEmail",
    "ParameterValue": "${NOTIFICATION_EMAIL:-}"
  }
]
EOF

# 4. CloudFormationスタックのデプロイ
echo -e "\n${GREEN}4. Deploying CloudFormation stack...${NC}"

if aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} 2>/dev/null; then
    echo "Updating existing stack..."
    aws cloudformation update-stack \
        --stack-name ${STACK_NAME} \
        --template-body file://aws/cloudformation-demo-trader.yaml \
        --parameters file://demo-trader-params.json \
        --capabilities CAPABILITY_IAM \
        --region ${REGION}
    
    echo "Waiting for stack update to complete..."
    aws cloudformation wait stack-update-complete --stack-name ${STACK_NAME} --region ${REGION}
else
    echo "Creating new stack..."
    aws cloudformation create-stack \
        --stack-name ${STACK_NAME} \
        --template-body file://aws/cloudformation-demo-trader.yaml \
        --parameters file://demo-trader-params.json \
        --capabilities CAPABILITY_IAM \
        --region ${REGION}
    
    echo "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME} --region ${REGION}
fi

# 5. デプロイ結果の確認
echo -e "\n${GREEN}5. Deployment completed! Checking status...${NC}"

# スタック出力の取得
OUTPUTS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --query "Stacks[0].Outputs" --region ${REGION})
echo -e "${YELLOW}Stack Outputs:${NC}"
echo ${OUTPUTS} | jq -r '.[] | "\(.OutputKey): \(.OutputValue)"'

# ECSサービスの状態確認
CLUSTER_NAME=$(echo ${OUTPUTS} | jq -r '.[] | select(.OutputKey=="ECSClusterName") | .OutputValue')
SERVICE_NAME=$(echo ${OUTPUTS} | jq -r '.[] | select(.OutputKey=="ServiceName") | .OutputValue')

echo -e "\n${YELLOW}ECS Service Status:${NC}"
aws ecs describe-services \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --query "services[0].{Status:status,RunningTasks:runningCount,DesiredTasks:desiredCount}" \
    --region ${REGION}

# ログの表示
echo -e "\n${GREEN}Recent logs:${NC}"
aws logs tail /ecs/phase1-demo-trader --since 5m --region ${REGION} || echo "No logs yet"

# クリーンアップ
rm -f demo-trader-params.json

echo -e "\n${GREEN}Deployment complete!${NC}"
echo -e "Monitor logs with: aws logs tail /ecs/phase1-demo-trader --follow --region ${REGION}"
echo -e "Check trades with: aws dynamodb scan --table-name phase1-trades --region ${REGION}"