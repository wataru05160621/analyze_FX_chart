# IAM権限設定手順

## 方法1: AWS CLIで権限を追加（推奨）

```bash
# 1. ポリシーを作成
aws iam create-policy \
  --policy-name fx-analyzer-deployment-policy \
  --policy-document file://aws/iam-policy-for-deployment.json \
  --description "Policy for FX Analyzer deployment and management"

# 2. ユーザーにポリシーをアタッチ
aws iam attach-user-policy \
  --user-name fx-analyzer-user \
  --policy-arn arn:aws:iam::455931011903:policy/fx-analyzer-deployment-policy
```

## 方法2: AWS Consoleから設定

1. **AWS Console** にログイン
2. **IAM** サービスに移動
3. **ユーザー** > `fx-analyzer-user` を選択
4. **許可** タブ > **許可を追加** > **ポリシーを直接アタッチ**
5. **ポリシーを作成** をクリック
6. **JSON** タブを選択
7. `aws/iam-policy-for-deployment.json` の内容を貼り付け
8. **次へ** をクリック
9. ポリシー名: `fx-analyzer-deployment-policy`
10. **ポリシーの作成** をクリック
11. 作成したポリシーを選択して **許可を追加**

## 方法3: 管理者権限を持つユーザーで実行

管理者権限を持つ別のユーザーがいる場合：

```bash
# 管理者プロファイルでポリシーを作成
aws iam create-policy \
  --policy-name fx-analyzer-deployment-policy \
  --policy-document file://aws/iam-policy-for-deployment.json \
  --profile admin

# fx-analyzer-userにポリシーをアタッチ
aws iam attach-user-policy \
  --user-name fx-analyzer-user \
  --policy-arn arn:aws:iam::455931011903:policy/fx-analyzer-deployment-policy \
  --profile admin
```

## 権限付与後の確認

```bash
# 権限が正しく付与されたか確認
aws iam list-attached-user-policies --user-name fx-analyzer-user

# Lambda関数へのアクセス確認
aws lambda get-function --function-name fx-analyzer-prod --region ap-northeast-1
```

## 必要な権限の説明

このポリシーには以下の権限が含まれています：

1. **Lambda管理**: 関数の作成・更新・実行
2. **EventBridge管理**: スケジュールルールの設定
3. **CloudFormation**: スタックの作成・更新
4. **S3**: チャート画像の保存・取得
5. **ECR**: Dockerイメージの管理
6. **Secrets Manager**: APIキーの安全な保存
7. **DynamoDB**: トレードデータの保存
8. **CloudWatch Logs**: ログの確認
9. **ECS**: コンテナサービスの管理
10. **SNS**: 通知の送信

## 最小権限の原則

本番環境では、実際に使用する機能に応じて権限を絞ることを推奨します。
現在のポリシーは、デプロイと運用に必要なすべての権限を含んでいます。