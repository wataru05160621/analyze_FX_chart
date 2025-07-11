#!/usr/bin/env python3
"""
環境変数の設定状況を確認
"""
import os
from pathlib import Path

def check_env_files():
    """環境変数ファイルの確認と読み込み"""
    print("=== 環境変数設定チェック ===\n")
    
    # .envファイル
    if os.path.exists('.env'):
        print("📄 .env ファイル:")
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if 'WORDPRESS' in key or 'TWITTER' in key:
                            if value and value != 'your_value_here':
                                print(f"   ✅ {key}: 設定済み")
                            else:
                                print(f"   ❌ {key}: 未設定")
        print()
    else:
        print("❌ .env ファイルが見つかりません\n")
    
    # .env.phase1ファイル
    if os.path.exists('.env.phase1'):
        print("📄 .env.phase1 ファイル:")
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if key in ['ENABLE_PHASE1', 'SLACK_WEBHOOK_URL', 'ENABLE_BLOG_POSTING']:
                            if value and value != 'your_value_here':
                                print(f"   ✅ {key}: {value[:50]}...")
                            else:
                                print(f"   ❌ {key}: 未設定")
        print()
    else:
        print("❌ .env.phase1 ファイルが見つかりません\n")
    
    # 必要な環境変数の確認
    print("📋 必要な環境変数の設定状況:\n")
    
    required_vars = {
        "基本設定": [
            "CLAUDE_API_KEY",
            "NOTION_API_KEY",
            "NOTION_DATABASE_ID"
        ],
        "Phase 1 (Slack)": [
            "ENABLE_PHASE1",
            "SLACK_WEBHOOK_URL"
        ],
        "ブログ投稿": [
            "ENABLE_BLOG_POSTING",
            "WORDPRESS_URL",
            "WORDPRESS_USERNAME",
            "WORDPRESS_PASSWORD"
        ],
        "X (Twitter)": [
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET"
        ],
        "価格取得": [
            "ALPHA_VANTAGE_API_KEY"
        ]
    }
    
    # 環境変数を読み込み
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # チェック
    for category, vars in required_vars.items():
        print(f"【{category}】")
        all_set = True
        for var in vars:
            value = os.environ.get(var, '')
            if value and value not in ['your_value_here', 'your_api_key_here', 'demo']:
                if 'KEY' in var or 'PASSWORD' in var:
                    print(f"   ✅ {var}: 設定済み")
                else:
                    print(f"   ✅ {var}: {value[:30]}...")
            else:
                print(f"   ❌ {var}: 未設定")
                all_set = False
        
        if all_set:
            print(f"   → {category}の機能は利用可能です")
        else:
            print(f"   → {category}の機能は利用できません")
        print()
    
    # 推奨設定
    print("💡 推奨設定:\n")
    
    if not os.environ.get('WORDPRESS_URL'):
        print("1. WordPress投稿を有効にするには:")
        print("   .envファイルに以下を追加:")
        print("   WORDPRESS_URL=https://your-site.com")
        print("   WORDPRESS_USERNAME=your_username")
        print("   WORDPRESS_PASSWORD=your_app_password")
        print()
    
    if not os.environ.get('TWITTER_API_KEY'):
        print("2. X (Twitter)投稿を有効にするには:")
        print("   .envファイルに以下を追加:")
        print("   TWITTER_API_KEY=your_api_key")
        print("   TWITTER_API_SECRET=your_api_secret")
        print("   TWITTER_ACCESS_TOKEN=your_access_token")
        print("   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret")
        print()
    
    if os.environ.get('ENABLE_PHASE1') != 'true':
        print("3. Phase 1 (Slack通知)を有効にするには:")
        print("   .env.phase1ファイルで:")
        print("   ENABLE_PHASE1=true")
        print()

if __name__ == "__main__":
    check_env_files()