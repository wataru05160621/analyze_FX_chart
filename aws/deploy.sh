#!/bin/bash
# AWS デプロイスクリプト

# 設定
AWS_REGION="ap-northeast-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="fx-analysis"
IMAGE_TAG="latest"
STACK_NAME="fx-analysis-stack"

echo "=== FX分析システム AWS デプロイ ==="
echo "リージョン: $AWS_REGION"
echo "アカウントID: $AWS_ACCOUNT_ID"
echo

# 1. ECRリポジトリ作成
echo "1. ECRリポジトリ作成..."
aws ecr create-repository \
    --repository-name $ECR_REPOSITORY \
    --region $AWS_REGION \
    2>/dev/null || echo "リポジトリは既に存在します"

# 2. Docker イメージビルド
echo "2. Docker イメージビルド..."
docker build -f Dockerfile.aws -t $ECR_REPOSITORY:$IMAGE_TAG .

# 3. ECRにログイン
echo "3. ECRログイン..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 4. イメージにタグ付け
echo "4. イメージタグ付け..."
docker tag $ECR_REPOSITORY:$IMAGE_TAG \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# 5. ECRにプッシュ
echo "5. ECRプッシュ..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# 6. CloudFormationスタック作成/更新
echo "6. CloudFormationデプロイ..."

# パラメータファイル作成
cat > parameters.json << EOF
[
  {
    "ParameterKey": "DockerImageUri",
    "ParameterValue": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
  },
  {
    "ParameterKey": "SlackWebhookUrl",
    "ParameterValue": "$SLACK_WEBHOOK_URL"
  }
]
EOF

# スタック作成または更新
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION >/dev/null 2>&1; then
    echo "スタック更新中..."
    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://aws/cloudformation-fx-analysis.yaml \
        --parameters file://parameters.json \
        --capabilities CAPABILITY_IAM \
        --region $AWS_REGION
else
    echo "スタック作成中..."
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://aws/cloudformation-fx-analysis.yaml \
        --parameters file://parameters.json \
        --capabilities CAPABILITY_IAM \
        --region $AWS_REGION
fi

# 7. デプロイ完了待機
echo "7. デプロイ完了待機中..."
aws cloudformation wait stack-create-complete \
    --stack-name $STACK_NAME \
    --region $AWS_REGION 2>/dev/null || \
aws cloudformation wait stack-update-complete \
    --stack-name $STACK_NAME \
    --region $AWS_REGION

# 8. 出力情報取得
echo "8. デプロイ完了!"
echo
echo "=== スタック出力 ==="
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs' \
    --output table

# クリーンアップ
rm -f parameters.json

echo
echo "=== 次のステップ ==="
echo "1. AWS Secrets Manager で各種APIキーを設定"
echo "   - fx-analysis/claude-api-key"
echo "   - fx-analysis/wordpress-credentials"
echo "   - fx-analysis/twitter-credentials"
echo "   - fx-analysis/notion-api-key"
echo
echo "2. Parameter Store で設定を更新"
echo "   - /fx-analysis/notion-database-id"
echo
echo "3. EventBridge ルールの確認"
echo "   - fx-analysis-8am (平日8時)"
echo "   - fx-analysis-3pm (平日15時)"
echo "   - fx-analysis-9pm (平日21時)"