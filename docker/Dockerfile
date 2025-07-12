# ECS Fargate用Dockerfile
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新とインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libfreetype6-dev \
    libpng-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をコピーしてインストール
COPY requirements-dev.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 必要なディレクトリを作成
RUN mkdir -p /app/screenshots /app/logs

# 環境変数を設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# ヘルスチェック用のスクリプト
COPY docker-healthcheck.py /app/
RUN chmod +x /app/docker-healthcheck.py

# ECSタスク用のエントリーポイント
CMD ["python", "ecs_task_script.py"]