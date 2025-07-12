# Claude AI コンテキスト情報

このファイルは、Claude AIがプロジェクトを理解するための重要な情報を含んでいます。

## 📁 プロジェクト構造

詳細は[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)を参照してください。

## 📚 ドキュメント一覧

**重要**: すべてのドキュメントは[docs/00_DOCUMENT_INDEX.md](docs/00_DOCUMENT_INDEX.md)で管理されています。
ドキュメントを探す場合は、まずこのインデックスファイルを参照してください。

### 主要ドキュメントへのクイックリンク
- [ドキュメント索引](docs/00_DOCUMENT_INDEX.md) - 全ドキュメントの一覧と概要
- [クイックスタート](docs/17_quick_start.md) - 30分で本番運用開始
- [プロジェクト構造](PROJECT_STRUCTURE.md) - ディレクトリ構成
- [パス移行ガイド](PATH_MIGRATION_GUIDE.md) - ファイルパスの変更情報

## 🎯 プロジェクト概要

**FXチャート自動分析システム**
- USD/JPYチャートを自動生成
- Claude 3.5 SonnetによるAI分析
- Notionデータベースに結果保存
- WordPress + X（Twitter）への自動投稿
- AWS ECS Fargate + S3で完全自動化

## 🔧 主要な実行コマンド

```bash
# メイン実行
python scripts/execution/execute_production.py

# ECSデプロイ
./scripts/deploy/deploy-ecs.sh

# Lambda更新
python scripts/setup/update_lambda_code.py
```

## 📋 作業時の注意事項

1. **ドキュメントを探す場合**
   - 必ず `docs/00_DOCUMENT_INDEX.md` を最初に確認
   - 連番管理されているため、カテゴリ別に整理されている

2. **新しいファイルを追加する場合**
   - 適切なディレクトリに配置（scripts/, docs/, tests/など）
   - ドキュメントの場合は連番を付けてインデックスを更新

3. **パスエラーが発生した場合**
   - `PATH_MIGRATION_GUIDE.md` を参照
   - 多くのファイルが移動されているため注意

## 🚀 現在の状態

- ✅ プロジェクト構造の整理完了（2025年1月）
- ✅ ECS Fargateでの定時実行稼働中
- ✅ Lambda関数による検証システム稼働中
- ✅ ドキュメント管理システム導入済み

## 🔍 トラブルシューティング

問題が発生した場合は、以下の順序で確認：
1. `docs/00_DOCUMENT_INDEX.md` で関連ドキュメントを検索
2. `docs/15_production_test.md` でトラブルシューティング手順を確認
3. `logs/` ディレクトリでエラーログを確認