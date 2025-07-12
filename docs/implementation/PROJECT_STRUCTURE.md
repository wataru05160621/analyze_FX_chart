# プロジェクト構造

FX分析システムのディレクトリ構造を整理しました。

## ディレクトリ構成

```
analyze_FX_chart/
├── src/                    # ソースコード
│   ├── main.py            # メインエントリーポイント
│   ├── chart_generator.py # チャート生成
│   ├── claude_analyzer.py # AI分析
│   ├── notion_writer.py   # Notion投稿
│   └── ...               # その他のモジュール
│
├── scripts/               # 実行スクリプト
│   ├── execution/        # 実行用スクリプト
│   ├── setup/           # セットアップスクリプト
│   └── deploy/          # デプロイスクリプト
│
├── aws/                  # AWS関連ファイル
│   ├── lambda関連
│   ├── CloudFormation
│   └── ECS/Fargate設定
│
├── docker/              # Docker関連
│   ├── Dockerfile      # 本番用
│   └── Dockerfile.*    # 各環境用
│
├── tests/              # テストコード
│   └── 各種テスト
│
├── docs/               # ドキュメント
│   ├── ガイド
│   ├── 設定方法
│   └── アーキテクチャ
│
├── config/             # 設定ファイル
│   ├── requirements.txt
│   └── 各種設定
│
├── screenshots/        # チャート画像
├── logs/              # ログファイル
├── performance/       # パフォーマンスデータ
└── archive/           # アーカイブ済みファイル
```

## 主要ファイルの場所

### 実行関連
- メイン実行: `scripts/execution/execute_production.py`
- Lambda実行: `aws/aws_lambda_function.py`
- ECS実行: `aws/ecs_task_script.py`

### デプロイ関連
- ECSデプロイ: `scripts/deploy/deploy-ecs.sh`
- Lambda更新: `scripts/setup/update_lambda_code.py`

### 設定関連
- Python依存関係: `config/requirements.txt`
- 環境変数テンプレート: `aws/lambda_env_vars_template.json`

### ドキュメント
- セットアップガイド: `docs/`
- アーキテクチャ: `doc/system_architecture.md`

## 注意事項
- 機密情報（.env, APIキーなど）はGitに含めない
- screenshotsディレクトリは定期的にクリーンアップ
- logsディレクトリは自動ローテーション設定済み