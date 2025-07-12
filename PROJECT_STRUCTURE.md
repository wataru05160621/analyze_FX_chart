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
│   ├── deploy/          # デプロイスクリプト
│   └── implementation/  # 実装関連スクリプト
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
├── docs/               # ドキュメント（連番管理）
│   ├── 00_DOCUMENT_INDEX.md  # ドキュメント索引
│   ├── 01-18_*.md           # 連番付きドキュメント
│   ├── reports/             # レポート・実行結果
│   ├── phase1/              # Phase1実装関連
│   ├── implementation/      # 実装・設定
│   └── analysis/           # 分析・比較
│
├── config/             # 設定ファイル
│   ├── requirements.txt
│   └── 各種設定
│
├── archive/            # アーカイブ済みファイル
│   ├── analysis_results/
│   └── misc/
│
├── screenshots/        # チャート画像
├── logs/              # ログファイル
└── performance/       # パフォーマンスデータ
```

## 主要ファイルの場所

### 実行関連
- メイン実行: `scripts/execution/execute_production.py`
- Lambda実行: `aws/aws_lambda_function.py`
- ECS実行: `scripts/execution/ecs_task_script.py`

### デプロイ関連
- ECSデプロイ: `scripts/deploy/deploy-ecs.sh`
- Lambda更新: `scripts/setup/update_lambda_code.py`

### 設定関連
- Python依存関係: `config/requirements.txt`
- 環境変数テンプレート: `aws/lambda_env_vars_template.json`

### ドキュメント
- **ドキュメント索引**: `docs/00_DOCUMENT_INDEX.md`
- セットアップガイド: `docs/01-05_*.md`
- コスト・AI関連: `docs/06-10_*.md`
- デプロイ・運用: `docs/11-14_*.md`
- 品質・テスト: `docs/15-17_*.md`
- 実装計画: `docs/18_*.md`

## 整理のポイント

1. **ルートディレクトリのクリーンアップ**
   - 実行スクリプトは `scripts/` へ
   - ドキュメントは `docs/` へ
   - 設定ファイルは `config/` へ

2. **ドキュメントの連番管理**
   - `00_DOCUMENT_INDEX.md` で全体を管理
   - カテゴリ別にサブディレクトリ整理

3. **スクリプトの用途別整理**
   - execution: 実行・投稿系
   - setup: 初期設定・更新系
   - deploy: デプロイ系
   - implementation: 実装・開発系

## 注意事項
- 機密情報（.env, APIキーなど）はGitに含めない
- screenshotsディレクトリは定期的にクリーンアップ
- logsディレクトリは自動ローテーション設定済み

## パス変更について
詳細は `PATH_MIGRATION_GUIDE.md` を参照してください。