#!/usr/bin/env python3
"""
Twitter API v2の設定確認スクリプト
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_twitter_auth():
    """Twitter API認証をチェック"""
    
    # Bearer Token を作成
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    
    print("=== Twitter API設定確認 ===")
    print(f"API Key: {api_key[:10]}...")
    print(f"API Secret: {api_secret[:10]}...")
    
    # Access Tokenで認証テスト
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    
    print(f"\nAccess Token: {access_token[:20]}...")
    print(f"Access Token Secret: {access_token_secret[:10]}...")
    
    # OAuth 1.0a認証でユーザー情報を取得
    import tweepy
    
    try:
        # v1.1 API（OAuth 1.0a）でテスト
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        api_v1 = tweepy.API(auth)
        
        print("\n=== Twitter API v1.1 テスト ===")
        user = api_v1.verify_credentials()
        print(f"✅ v1.1 認証成功: @{user.screen_name}")
        
        # v2 API でテスト
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        print("\n=== Twitter API v2 テスト ===")
        me = client.get_me()
        if me.data:
            print(f"✅ v2 認証成功: @{me.data.username}")
        else:
            print("❌ v2 認証失敗: ユーザー情報を取得できません")
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        
        if "403" in str(e):
            print("\n対処法:")
            print("1. Developer Portalでプロジェクトを確認")
            print("2. アプリがプロジェクトに紐付いているか確認")
            print("3. User authentication settingsでOAuth 2.0を有効化")
            print("4. App permissionsを'Read and write'に設定")

if __name__ == "__main__":
    check_twitter_auth()