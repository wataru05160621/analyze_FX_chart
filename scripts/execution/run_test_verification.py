import subprocess
import sys

result = subprocess.run([sys.executable, "test_verification_day.py"], cwd="/Users/shinzato/programing/claude_code/analyze_FX_chart")
sys.exit(result.returncode)