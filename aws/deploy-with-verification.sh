#!/bin/bash

# 検証日数機能を含む最新版のデプロイスクリプト
set -e

echo "=== FX Analysis with Verification Day - AWS Deployment ==="

# 環境変数チェック
required_vars=("CLAUDE_API_KEY" "SLACK_WEBHOOK_URL" "WORDPRESS_URL" "WORDPRESS_USERNAME" "WORDPRESS_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=($var)
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ 以下の環境変数が設定されていません:"
    printf '%s\n' "${missing_vars[@]}"
    echo ""
    echo "以下のコマンドで設定してください:"
    for var in "${missing_vars[@]}"; do
        echo "export $var=your_value_here"
    done
    exit 1
fi

# AWS設定
REGION=${AWS_REGION:-ap-northeast-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
STACK_NAME="fx-analysis-stack"
IMAGE_NAME="fx-analysis"

echo "AWS Account: $ACCOUNT_ID"
echo "Region: $REGION"
echo ""

# 1. ECRリポジトリ確認/作成
echo "1. ECRリポジトリの準備..."
if ! aws ecr describe-repositories --repository-names $IMAGE_NAME --region $REGION 2>/dev/null; then
    aws ecr create-repository --repository-name $IMAGE_NAME --region $REGION
    echo "✅ ECRリポジトリ作成完了"
else
    echo "✅ ECRリポジトリは既に存在"
fi

# 2. Dockerイメージのビルドとプッシュ
echo ""
echo "2. Dockerイメージのビルドとプッシュ..."

# Dockerfileの更新（検証日数機能を含む）
cat > Dockerfile.aws << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# システムパッケージ
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-ipafont-gothic \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 環境変数
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Pythonパッケージ
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY src/ ./src/
COPY doc/ ./doc/
COPY *.py ./

# 検証日数トラッカーファイル用ディレクトリ
RUN mkdir -p /app/data

# エントリーポイント
CMD ["python", "aws_lambda_function.py"]
EOF

# ビルドとプッシュ
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker build -f Dockerfile.aws -t $IMAGE_NAME .
docker tag $IMAGE_NAME:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$IMAGE_NAME:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$IMAGE_NAME:latest

echo "✅ Dockerイメージのプッシュ完了"

# 3. CloudFormationパラメータ
echo ""
echo "3. CloudFormationパラメータの準備..."

cat > cf-params.json << EOF
[
  {
    "ParameterKey": "ImageUri",
    "ParameterValue": "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$IMAGE_NAME:latest"
  }
]
EOF

# 4. CloudFormationデプロイ
echo ""
echo "4. CloudFormationスタックのデプロイ..."

# シークレットの更新
echo "シークレットを更新中..."

# Claude API Key
aws secretsmanager put-secret-value \
    --secret-id fx-analysis/claude-api-key \
    --secret-string "{\"api_key\":\"$CLAUDE_API_KEY\"}" \
    --region $REGION 2>/dev/null || \
aws secretsmanager create-secret \
    --name fx-analysis/claude-api-key \
    --secret-string "{\"api_key\":\"$CLAUDE_API_KEY\"}" \
    --region $REGION

# WordPress Credentials
aws secretsmanager put-secret-value \
    --secret-id fx-analysis/wordpress-credentials \
    --secret-string "{\"url\":\"$WORDPRESS_URL\",\"username\":\"$WORDPRESS_USERNAME\",\"password\":\"$WORDPRESS_PASSWORD\"}" \
    --region $REGION 2>/dev/null || \
aws secretsmanager create-secret \
    --name fx-analysis/wordpress-credentials \
    --secret-string "{\"url\":\"$WORDPRESS_URL\",\"username\":\"$WORDPRESS_USERNAME\",\"password\":\"$WORDPRESS_PASSWORD\"}" \
    --region $REGION

# スタックのデプロイ/更新
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION 2>/dev/null; then
    echo "既存スタックを更新中..."
    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://aws/cloudformation-fx-analysis.yaml \
        --parameters file://cf-params.json \
        --capabilities CAPABILITY_IAM \
        --region $REGION
    
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION
else
    echo "新規スタックを作成中..."
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://aws/cloudformation-fx-analysis.yaml \
        --parameters file://cf-params.json \
        --capabilities CAPABILITY_IAM \
        --region $REGION
    
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION
fi

echo "✅ CloudFormationデプロイ完了"

# 5. 検証開始日の初期化（S3）
echo ""
echo "5. 検証開始日の初期化..."

# S3バケット名を取得
S3_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='S3BucketName'].OutputValue" \
    --output text \
    --region $REGION)

# 検証開始日ファイルをS3にアップロード（存在しない場合のみ）
if ! aws s3 ls s3://$S3_BUCKET/phase1_start_date.json 2>/dev/null; then
    echo "{\"start_date\":\"$(date -u +%Y-%m-%dT%H:%M:%S)\",\"phase\":\"Phase1\",\"description\":\"FXスキャルピング検証プロジェクト\"}" > phase1_start_date.json
    aws s3 cp phase1_start_date.json s3://$S3_BUCKET/phase1_start_date.json
    echo "✅ 検証開始日を初期化しました"
else
    echo "✅ 検証開始日は既に設定されています"
fi

# クリーンアップ
rm -f cf-params.json Dockerfile.aws phase1_start_date.json

# 6. デプロイ完了
echo ""
echo "=== デプロイ完了 ==="
echo ""
echo "📊 検証日数機能が有効になりました"
echo "📅 毎日以下の時間に自動実行されます:"
echo "   - 8:00 (全プラットフォーム投稿)"
echo "   - 15:00 (Notionのみ)"
echo "   - 21:00 (Notionのみ)"
echo ""
echo "🔍 確認方法:"
echo "   CloudWatch Logs: aws logs tail /aws/lambda/fx-analysis-function --follow"
echo "   実行履歴: AWS Console > Lambda > fx-analysis-function > Monitor"
echo ""
echo "✅ すべての設定が完了しました！"