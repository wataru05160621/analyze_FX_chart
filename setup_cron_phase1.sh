#!/bin/bash
# Phase 1: Cronジョブ設定スクリプト

echo "=== Phase 1 Cronジョブ設定 ==="
echo ""

# プロジェクトディレクトリを取得
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

# ログディレクトリを作成
mkdir -p "$PROJECT_DIR/logs"

# Cronジョブの内容を作成
CRON_CONTENT="# FX Trading Alert System - Phase 1
# 毎日 8:00, 15:00, 21:00 に実行
0 8,15,21 * * * cd $PROJECT_DIR && $PYTHON_PATH src/phase1_integration.py >> logs/phase1_$(date +\%Y\%m).log 2>&1"

echo "以下のCronジョブを設定します:"
echo "$CRON_CONTENT"
echo ""

# 現在のcrontabを一時ファイルに保存
crontab -l > /tmp/current_cron 2>/dev/null || true

# 既存のPhase 1エントリを削除（重複防止）
grep -v "phase1_integration.py" /tmp/current_cron > /tmp/new_cron || true

# 新しいエントリを追加
echo "" >> /tmp/new_cron
echo "$CRON_CONTENT" >> /tmp/new_cron

echo "Cronジョブを更新しますか？ (y/n)"
read -r response

if [ "$response" = "y" ]; then
    # Crontabを更新
    crontab /tmp/new_cron
    echo "✅ Cronジョブを設定しました"
    echo ""
    echo "現在のCronジョブ:"
    crontab -l | grep phase1_integration
else
    echo "Cronジョブの設定をキャンセルしました"
    echo ""
    echo "手動で設定する場合は以下のコマンドを使用してください:"
    echo "crontab -e"
    echo ""
    echo "そして以下の行を追加してください:"
    echo "$CRON_CONTENT"
fi

# 一時ファイルを削除
rm -f /tmp/current_cron /tmp/new_cron

echo ""
echo "ログファイルの確認方法:"
echo "tail -f $PROJECT_DIR/logs/phase1_$(date +%Y%m).log"