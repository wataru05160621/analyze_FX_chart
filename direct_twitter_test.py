#!/usr/bin/env python3
"""
Twitterへの直接投稿テスト
"""
import tweepy
from datetime import datetime

# Twitter API設定
api_key = "9lTKMamtQOrgxRn5Q87hcbJ07"
api_secret = "dRIUSBtg31YCf9u112Iy9pC6uHY75SFv67MoEx75nf0M0lz2Xm"
access_token = "1939874444509691904-B5JJStts2wtuOHAJD4vebzEq6RTXRb"
access_token_secret = "Et0qR6WOHkKPPffcDA6aCZIzhqIZyi1xs5pJBoWahW1Tq"

print("=== Twitter直接投稿テスト ===")
print()

try:
    # 認証
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    # API v1.1（より安定）
    api = tweepy.API(auth)
    
    # テストツイート
    tweet_text = f"""【テスト】FX分析システム
    
実行時刻: {datetime.now().strftime('%H:%M')}

これは自動投稿テストです。
正常に投稿されていれば、Twitter連携は正しく機能しています。

#FXテスト #自動投稿テスト"""
    
    print("ツイート内容:")
    print(tweet_text)
    print(f"\n文字数: {len(tweet_text)}")
    
    # 投稿
    tweet = api.update_status(tweet_text)
    
    print(f"\n✅ ツイート成功!")
    print(f"   ツイートID: {tweet.id}")
    print(f"   URL: https://twitter.com/user/status/{tweet.id}")
    
except tweepy.TweepyException as e:
    print(f"❌ Twitter APIエラー: {e}")
    
    # API v2で再試行
    try:
        print("\nAPI v2で再試行...")
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        response = client.create_tweet(text=tweet_text)
        if response.data:
            print(f"✅ ツイート成功 (v2)!")
            print(f"   ツイートID: {response.data['id']}")
    except Exception as e2:
        print(f"❌ v2でも失敗: {e2}")
        
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()

print("\nTwitterで確認してください")