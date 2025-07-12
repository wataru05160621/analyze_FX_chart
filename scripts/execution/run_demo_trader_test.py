#!/usr/bin/env python3
import subprocess
import sys

# Pythonスクリプトを直接実行
result = subprocess.run([sys.executable, "test_demo_trader_local.py"], cwd="/Users/shinzato/programing/claude_code/analyze_FX_chart")
sys.exit(result.returncode)