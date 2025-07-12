# パス移行ガイド

ディレクトリ構造の整理に伴う、ファイルパスの変更一覧です。

## 🔄 主なパス変更

### 設定ファイル
- `requirements.txt` → `config/requirements.txt`
- `requirements-dev.txt` → `config/requirements-dev.txt`
- `.env` → ルートのまま（変更なし）

### 実行スクリプト
- `execute_*.py` → `scripts/execution/execute_*.py`
- `run_*.py` → `scripts/execution/run_*.py`
- `run_*.sh` → `scripts/execution/run_*.sh`

### セットアップスクリプト
- `setup*.py` → `scripts/setup/setup*.py`
- `fix_*.py` → `scripts/setup/fix_*.py`
- `create_*.py` → `scripts/setup/create_*.py`
- `update_*.py` → `scripts/setup/update_*.py`

### デプロイスクリプト
- `deploy*.sh` → `scripts/deploy/deploy*.sh`

### AWS関連
- `aws_lambda_*.py` → `aws/aws_lambda_*.py`
- `lambda_*.py` → `aws/lambda_*.py`
- `template*.yaml` → `aws/template*.yaml`
- `*taskdef.json` → `aws/*taskdef.json`

### Docker関連
- `Dockerfile*` → `docker/Dockerfile*`
- `docker-healthcheck.py` → `docker/docker-healthcheck.py`

### テストファイル
- `test_*.py` → `tests/test_*.py`

## ⚠️ 注意事項

### 相対パスを使用しているファイル

1. **Docker関連**
   - Dockerfileの`COPY`コマンドは、ビルドコンテキストからの相対パスのため変更不要
   - ビルド時のコマンドは変わりません: `docker build -f docker/Dockerfile -t image-name .`

2. **AWS関連**
   - CloudFormationテンプレート内のパス参照は特に変更不要
   - デプロイスクリプト内のパスは既に調整済み

3. **Python imports**
   - `src/`ディレクトリ内のインポートは変更不要
   - ルートからの実行を想定している場合は変更不要

## 🛠️ 移行後の実行方法

### 実行スクリプト
```bash
# 旧
python execute_production.py

# 新
python scripts/execution/execute_production.py
```

### セットアップ
```bash
# 旧
python setup_eventbridge_schedule.py

# 新
python scripts/setup/setup_eventbridge_schedule.py
```

### デプロイ
```bash
# 旧
./deploy-ecs.sh

# 新
./scripts/deploy/deploy-ecs.sh
```

### テスト
```bash
# 旧
python test_full_flow.py

# 新
python tests/test_full_flow.py
```

## 📝 設定ファイルの参照

環境によっては設定ファイルのパスを更新する必要があります：

```python
# requirements.txtを参照する場合
# 旧
pip install -r requirements.txt

# 新
pip install -r config/requirements.txt
```

## 🔍 パスの確認方法

移行後にパスエラーが発生した場合：

1. エラーメッセージでファイル名を確認
2. 以下のコマンドで新しい場所を検索：
   ```bash
   find . -name "ファイル名" -type f
   ```
3. 必要に応じてパスを更新

## 📌 よくある質問

**Q: Dockerビルドが失敗する**
A: `docker build -f docker/Dockerfile .` のようにDockerfileのパスを指定してください

**Q: Pythonスクリプトが見つからない**
A: 新しいパス（scripts/execution/など）を確認してください

**Q: インポートエラーが発生する**
A: プロジェクトルートから実行しているか確認してください