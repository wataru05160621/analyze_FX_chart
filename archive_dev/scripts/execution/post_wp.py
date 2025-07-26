import requests
import base64
from datetime import datetime

# WordPress投稿
url = "https://by-price-action.com/wp-json/wp/v2/posts"
auth = base64.b64encode(b"publish:aFIxNNhft0lSjkzwI75rYZk2").decode()

data = {
    'title': f'テスト投稿 {datetime.now().strftime("%H:%M")}',
    'content': '<p>FX分析システムからのテスト投稿です。</p>',
    'status': 'draft'
}

headers = {
    'Authorization': f'Basic {auth}',
    'Content-Type': 'application/json'
}

resp = requests.post(url, json=data, headers=headers)
print(f"WordPress: {resp.status_code}")
if resp.status_code == 201:
    print(f"成功! URL: {resp.json()['link']}")
else:
    print(resp.text[:200])