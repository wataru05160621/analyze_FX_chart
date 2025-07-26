#!/usr/bin/env python3
import subprocess
import os
import sys

# 作業ディレクトリを設定
os.chdir("/Users/shinzato/programing/claude_code/analyze_FX_chart")

# git pushスクリプトを実行
result = subprocess.run([sys.executable, "git_push.py"])
sys.exit(result.returncode)