#!/bin/bash
# FX分析のcronジョブを設定するスクリプト

# プロジェクトのディレクトリを取得
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Python環境のパスを取得
PYTHON_PATH="$(which python3)"

# cronジョブの内容を定義
CRON_JOBS="
# FX Chart Analysis - JST 8:00, 15:00, 21:00
0 8 * * * cd $PROJECT_DIR && $PYTHON_PATH run_scheduler.py --once >> $PROJECT_DIR/logs/cron.log 2>&1
0 15 * * * cd $PROJECT_DIR && $PYTHON_PATH run_scheduler.py --once >> $PROJECT_DIR/logs/cron.log 2>&1
0 21 * * * cd $PROJECT_DIR && $PYTHON_PATH run_scheduler.py --once >> $PROJECT_DIR/logs/cron.log 2>&1
"

echo "現在のcronジョブ:"
crontab -l 2>/dev/null

echo ""
echo "以下のcronジョブを追加しますか？"
echo "$CRON_JOBS"
echo ""
read -p "続行しますか？ (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    # 既存のcronジョブを取得
    (crontab -l 2>/dev/null; echo "$CRON_JOBS") | crontab -
    echo "cronジョブを追加しました。"
    echo ""
    echo "現在のcronジョブ:"
    crontab -l
else
    echo "キャンセルしました。"
fi