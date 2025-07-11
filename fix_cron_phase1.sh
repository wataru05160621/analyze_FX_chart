#!/bin/bash
# Phase 1: Cronジョブ修正スクリプト

echo "=== Phase 1 Cronジョブ修正 ==="
echo ""
echo "現在の問題:"
echo "- phase1_integration.py はSlackアラートのみ"
echo "- main_multi_currency.py がNotion、ブログ、X投稿を含む"
echo ""

# 現在のcrontabを一時ファイルに保存
crontab -l > /tmp/current_cron 2>/dev/null || true

# Phase 1の誤った設定を削除
grep -v "phase1_integration.py" /tmp/current_cron > /tmp/new_cron || true

# 正しい設定を追加
PROJECT_DIR="/Users/shinzato/programing/claude_code/analyze_FX_chart"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python3"

echo "" >> /tmp/new_cron
echo "# FX分析システム - 修正版" >> /tmp/new_cron
echo "# 8:00 - 3通貨分析 + Notion/ブログ/X投稿" >> /tmp/new_cron
echo "0 8 * * * cd $PROJECT_DIR && $PYTHON_PATH -m src.main_multi_currency >> logs/fx_analysis_$(date +\%Y\%m).log 2>&1" >> /tmp/new_cron
echo "# 15:00, 21:00 - USD/JPY分析のみ" >> /tmp/new_cron
echo "0 15,21 * * * cd $PROJECT_DIR && $PYTHON_PATH -m src.main_multi_currency >> logs/fx_analysis_$(date +\%Y\%m).log 2>&1" >> /tmp/new_cron

echo "新しいCronジョブ設定:"
cat /tmp/new_cron | grep -E "(FX分析|8:00|15:00|21:00)"
echo ""

echo "Cronジョブを更新しますか？ (y/n)"
read -r response

if [ "$response" = "y" ]; then
    crontab /tmp/new_cron
    echo "✅ Cronジョブを更新しました"
else
    echo "更新をキャンセルしました"
fi

# 一時ファイルを削除
rm -f /tmp/current_cron /tmp/new_cron

echo ""
echo "テスト実行:"
echo "cd $PROJECT_DIR && $PYTHON_PATH -m src.main_multi_currency"