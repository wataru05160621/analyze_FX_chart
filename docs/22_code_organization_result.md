# コード整理結果

## 🎯 整理の目的
本番環境で実際に動作しているコードと、開発・テスト用コードを明確に分離し、混同を防ぐ。

## 📁 整理後のディレクトリ構成

### 本番環境コード（プロジェクトルート）

```
analyze_FX_chart/
├── src/                        # 本番で使用されるコアモジュール（15ファイル）
│   ├── main_multi_currency.py  # ECSエントリーポイント
│   ├── chart_generator.py      # チャート生成
│   ├── claude_analyzer.py      # AI分析
│   ├── notion_writer.py        # Notion投稿
│   ├── notion_analyzer.py      # Notion詳細分析
│   ├── blog_publisher.py       # WordPress/X投稿
│   ├── multi_currency_analyzer_optimized.py  # マルチ通貨分析
│   ├── blog_analyzer.py        # ブログ分析
│   ├── config.py              # 設定管理
│   ├── logger.py              # ロギング
│   ├── error_handler.py       # エラーハンドリング
│   ├── image_uploader.py      # 画像アップロード
│   ├── verification_tracker.py # 検証追跡
│   ├── lambda_main.py         # Lambda用
│   └── __init__.py
│
├── scripts/
│   ├── execution/
│   │   └── execute_production.py  # 本番実行スクリプト
│   ├── deploy/
│   │   └── deploy-ecs.sh         # ECSデプロイ
│   └── setup/
│       └── update_lambda_code.py  # Lambda更新
│
└── aws/
    ├── lambda_handler.py      # Lambdaハンドラー
    └── taskdef-v25.json       # ECSタスク定義
```

### アーカイブされた開発・テスト用コード

```
archive_dev/                    # 開発・テスト用（78ファイル）
├── src/                       # 未使用モジュール（23ファイル）
│   ├── phase1_*.py           # Phase1関連（未実装）
│   ├── tradingview_*.py      # TradingView関連
│   ├── slack_*.py            # Slack関連
│   ├── main.py               # 旧メインファイル
│   ├── scheduler.py          # ローカルスケジューラー
│   └── その他テスト用モジュール
│
├── scripts/                   # テストスクリプト（54ファイル）
│   ├── execution/
│   │   ├── run_*.py          # 各種実行スクリプト
│   │   ├── execute_*.py      # テスト実行
│   │   ├── debug_*.py        # デバッグツール
│   │   └── post_*.py         # 投稿テスト
│   └── その他スクリプト
│
└── README.md                  # アーカイブ説明
```

## 📊 整理結果

### ファイル数の変化
- **src/ディレクトリ**: 38ファイル → 15ファイル（61%削減）
- **scripts/execution/**: 55ファイル → 1ファイル（98%削減）
- **合計**: 78ファイルをアーカイブ

### 本番環境の明確化
- ECS Fargateで実行される最小限のファイルのみ保持
- 開発・テスト用コードは`archive_dev/`に隔離
- 新規開発者にとって理解しやすい構成

## 🔄 実行フロー（本番環境）

```
EventBridge (朝8時)
    ↓
ECS Fargate Task
    ↓
Dockerfile CMD: python -m src.main_multi_currency
    ↓
main_multi_currency.py
    ├── chart_generator.py → チャート生成
    ├── claude_analyzer.py → AI分析
    ├── notion_writer.py → Notion保存
    └── blog_publisher.py → WordPress投稿（8時のみ）
```

## 📝 今後の開発ガイドライン

1. **新機能の開発**
   - まず`archive_dev/`で開発・テスト
   - 本番投入時のみプロジェクトルートに移動

2. **テストスクリプト**
   - `archive_dev/scripts/`に作成
   - 本番環境を汚染しない

3. **Phase1機能**
   - 現在は`archive_dev/`に保管
   - 有効化時に必要なファイルのみ移動

## ⚠️ 注意事項

- `archive_dev/`内のファイルは本番環境では動作しません
- 必要なファイルの復元は慎重に行ってください
- 新しいテストコードは直接`archive_dev/`に作成してください

---
整理実施日: 2025年1月