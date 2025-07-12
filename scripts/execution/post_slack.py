import requests
from datetime import datetime

# Slack通知
webhook = "https://hooks.slack.com/services/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"
message = {
    "text": f"FX分析システムテスト {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
}

resp = requests.post(webhook, json=message)
print(f"Slack: {resp.status_code}")
if resp.status_code == 200:
    print("成功!")
else:
    print(resp.text)