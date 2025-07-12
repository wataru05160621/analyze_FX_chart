#!/usr/bin/env python3
"""
WordPressへの直接投稿テスト
"""
import requests
import base64
from datetime import datetime

# WordPress設定
wp_url = "https://by-price-action.com"
wp_user = "publish"
wp_pass = "aFIxNNhft0lSjkzwI75rYZk2"

print("=== WordPress直接投稿テスト ===")
print(f"URL: {wp_url}")
print(f"ユーザー: {wp_user}")
print()

# 認証ヘッダー作成
credentials = f"{wp_user}:{wp_pass}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
headers = {
    'Authorization': f'Basic {encoded_credentials}',
    'Content-Type': 'application/json'
}

# テスト投稿データ
post_data = {
    'title': f'【テスト】FX分析システム投稿テスト {datetime.now().strftime("%Y-%m-%d %H:%M")}',
    'content': f'''<p>これはFX分析システムからの自動投稿テストです。</p>

<p>実行時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

<h2>テスト内容</h2>
<ul>
<li>WordPress API接続: テスト中</li>
<li>自動投稿機能: テスト中</li>
<li>画像アップロード: 未実施</li>
</ul>

<p>正常に投稿されていれば、WordPress設定は正しく機能しています。</p>

<hr>
<p><em>※これはテスト投稿です。</em></p>''',
    'status': 'draft',  # 下書きとして投稿
    'categories': [],
    'tags': []
}

# 投稿実行
try:
    url = f"{wp_url}/wp-json/wp/v2/posts"
    print(f"投稿先: {url}")
    
    response = requests.post(url, headers=headers, json=post_data)
    
    print(f"レスポンスコード: {response.status_code}")
    
    if response.status_code == 201:
        post_info = response.json()
        print(f"✅ 投稿成功!")
        print(f"   投稿ID: {post_info['id']}")
        print(f"   URL: {post_info['link']}")
        print(f"   ステータス: {post_info['status']}")
    else:
        print(f"❌ 投稿失敗")
        print(f"エラー内容: {response.text}")
        
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()

print("\nWordPress管理画面で確認してください:")
print(f"{wp_url}/wp-admin/edit.php")