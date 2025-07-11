#!/usr/bin/env python3
"""
実際に投稿を実行
"""
import os
import sys
from datetime import datetime

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== FX分析システム 実投稿実行 ===")
print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 環境変数を手動で設定
os.environ['WORDPRESS_URL'] = 'https://by-price-action.com'
os.environ['WORDPRESS_USERNAME'] = 'publish'
os.environ['WORDPRESS_PASSWORD'] = 'aFIxNNhft0lSjkzwI75rYZk2'
os.environ['TWITTER_API_KEY'] = '9lTKMamtQOrgxRn5Q87hcbJ07'
os.environ['TWITTER_API_SECRET'] = 'dRIUSBtg31YCf9u112Iy9pC6uHY75SFv67MoEx75nf0M0lz2Xm'
os.environ['TWITTER_ACCESS_TOKEN'] = '1939874444509691904-B5JJStts2wtuOHAJD4vebzEq6RTXRb'
os.environ['TWITTER_ACCESS_TOKEN_SECRET'] = 'Et0qR6WOHkKPPffcDA6aCZIzhqIZyi1xs5pJBoWahW1Tq'

# .env.phase1の設定
os.environ['ENABLE_PHASE1'] = 'true'
os.environ['SLACK_WEBHOOK_URL'] = 'https://hooks.slack.com/services/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'

# 実行
try:
    # 1. WordPress投稿テスト
    print("1. WordPress投稿:")
    import requests
    import base64
    
    credentials = f"{os.environ['WORDPRESS_USERNAME']}:{os.environ['WORDPRESS_PASSWORD']}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {encoded}',
        'Content-Type': 'application/json'
    }
    
    post_data = {
        'title': f'FX分析システム投稿テスト {datetime.now().strftime("%m月%d日 %H:%M")}',
        'content': f'''<p>FX分析システムからの自動投稿テストです。</p>
<p>実行時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
<h2>システム状態</h2>
<ul>
<li>WordPress連携: ✅ 正常</li>
<li>自動投稿: ✅ 実行中</li>
</ul>
<p><em>※これはテスト投稿です。</em></p>''',
        'status': 'draft'
    }
    
    response = requests.post(
        f"{os.environ['WORDPRESS_URL']}/wp-json/wp/v2/posts",
        headers=headers,
        json=post_data
    )
    
    if response.status_code == 201:
        post_info = response.json()
        print(f"   ✅ 成功! ID: {post_info['id']}, URL: {post_info['link']}")
    else:
        print(f"   ❌ 失敗: {response.status_code} - {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ エラー: {e}")

# 2. Slack通知
print("\n2. Slack通知:")
try:
    import requests
    
    slack_message = {
        "text": f"🧪 FX分析システム投稿テスト\\n実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n状態: WordPress投稿テスト完了"
    }
    
    response = requests.post(os.environ['SLACK_WEBHOOK_URL'], json=slack_message)
    
    if response.status_code == 200:
        print("   ✅ Slack通知送信成功")
    else:
        print(f"   ❌ 失敗: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ エラー: {e}")

# 3. Twitter投稿
print("\n3. Twitter投稿:")
try:
    import tweepy
    
    auth = tweepy.OAuthHandler(
        os.environ['TWITTER_API_KEY'],
        os.environ['TWITTER_API_SECRET']
    )
    auth.set_access_token(
        os.environ['TWITTER_ACCESS_TOKEN'],
        os.environ['TWITTER_ACCESS_TOKEN_SECRET']
    )
    
    api = tweepy.API(auth)
    
    tweet_text = f"""【テスト】FX分析システム

実行時刻: {datetime.now().strftime('%H:%M')}
自動投稿テストを実行しました。

#FX分析 #システムテスト"""
    
    tweet = api.update_status(tweet_text)
    print(f"   ✅ 成功! ID: {tweet.id}")
    print(f"      URL: https://twitter.com/user/status/{tweet.id}")
    
except Exception as e:
    print(f"   ❌ エラー: {e}")
    # V2で再試行
    try:
        print("   API v2で再試行...")
        client = tweepy.Client(
            consumer_key=os.environ['TWITTER_API_KEY'],
            consumer_secret=os.environ['TWITTER_API_SECRET'],
            access_token=os.environ['TWITTER_ACCESS_TOKEN'],
            access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET']
        )
        
        response = client.create_tweet(text=tweet_text)
        if response.data:
            print(f"   ✅ 成功! (v2) ID: {response.data['id']}")
    except Exception as e2:
        print(f"   ❌ v2も失敗: {e2}")

print("\n" + "="*50)
print("投稿結果を各プラットフォームで確認してください:")
print("- WordPress: https://by-price-action.com/wp-admin/")
print("- Slack: 設定したチャンネル")
print("- Twitter: タイムライン")
print("="*50)