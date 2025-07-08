#!/bin/bash
# 現在時刻でFX分析を実行（ブログ投稿込み）

echo "=== FX分析実行 ==="
echo "時刻: $(date '+%Y-%m-%d %H:%M:%S JST')"
echo "ブログ投稿: 有効（ENABLE_BLOG_POSTING=true）"
echo

# 仮想環境のPythonを使用
cd /Users/shinzato/programing/claude_code/analyze_FX_chart
/Users/shinzato/programing/claude_code/analyze_FX_chart/venv/bin/python -m src.main