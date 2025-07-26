import subprocess
import sys
import os

# 環境変数をクリア（シェル環境の問題を回避）
clean_env = os.environ.copy()
clean_env.pop('SHELL', None)
clean_env.pop('ZDOTDIR', None)

# safe_git_push.pyを実行
result = subprocess.run(
    [sys.executable, 'safe_git_push.py'],
    cwd='/Users/shinzato/programing/claude_code/analyze_FX_chart',
    env=clean_env
)
sys.exit(result.returncode)