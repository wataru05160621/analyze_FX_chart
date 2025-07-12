#!/usr/bin/env python3
"""
WordPressのカテゴリとタグを設定するスクリプト
"""
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# WordPress認証設定
wp_url = os.getenv("WORDPRESS_URL")
wp_username = os.getenv("WORDPRESS_USERNAME")
wp_password = os.getenv("WORDPRESS_PASSWORD")

# 認証ヘッダー作成
credentials = f"{wp_username}:{wp_password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
headers = {
    'Authorization': f'Basic {encoded_credentials}',
    'Content-Type': 'application/json'
}

def get_or_create_category(name, slug):
    """カテゴリを取得または作成"""
    # 既存カテゴリを検索
    url = f"{wp_url}/wp-json/wp/v2/categories"
    params = {'search': name}
    response = requests.get(url, headers=headers, params=params)
    
    categories = response.json()
    for cat in categories:
        if cat['name'] == name:
            print(f"✓ カテゴリ '{name}' は既に存在します (ID: {cat['id']})")
            return cat['id']
    
    # カテゴリを作成
    data = {
        'name': name,
        'slug': slug
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        cat_id = response.json()['id']
        print(f"✅ カテゴリ '{name}' を作成しました (ID: {cat_id})")
        return cat_id
    else:
        print(f"❌ カテゴリ作成エラー: {response.text}")
        return None

def get_or_create_tag(name, slug):
    """タグを取得または作成"""
    # 既存タグを検索
    url = f"{wp_url}/wp-json/wp/v2/tags"
    params = {'search': name}
    response = requests.get(url, headers=headers, params=params)
    
    tags = response.json()
    for tag in tags:
        if tag['name'] == name:
            print(f"✓ タグ '{name}' は既に存在します (ID: {tag['id']})")
            return tag['id']
    
    # タグを作成
    data = {
        'name': name,
        'slug': slug
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        tag_id = response.json()['id']
        print(f"✅ タグ '{name}' を作成しました (ID: {tag_id})")
        return tag_id
    else:
        print(f"❌ タグ作成エラー: {response.text}")
        return None

def main():
    """カテゴリとタグをセットアップ"""
    print("=== WordPress タクソノミー設定 ===")
    print(f"サイト: {wp_url}")
    print()
    
    # カテゴリを作成
    print("カテゴリを設定中...")
    category_ids = {
        'ドル円': get_or_create_category('ドル円', 'usdjpy'),
        '分析': get_or_create_category('分析', 'analysis')
    }
    
    print()
    
    # タグを作成
    print("タグを設定中...")
    tag_ids = {
        '日次ドル円分析': get_or_create_tag('日次ドル円分析', 'daily-usdjpy-analysis')
    }
    
    print()
    print("=== 設定完了 ===")
    print("カテゴリID:")
    for name, id in category_ids.items():
        if id:
            print(f"  {name}: {id}")
    
    print("\nタグID:")
    for name, id in tag_ids.items():
        if id:
            print(f"  {name}: {id}")
    
    # 設定ファイルに保存
    config = f"""
# WordPress タクソノミー設定
WORDPRESS_CATEGORY_USDJPY={category_ids.get('ドル円', '')}
WORDPRESS_CATEGORY_ANALYSIS={category_ids.get('分析', '')}
WORDPRESS_TAG_DAILY_USDJPY={tag_ids.get('日次ドル円分析', '')}
"""
    
    with open('wordpress_taxonomy.conf', 'w', encoding='utf-8') as f:
        f.write(config)
    
    print(f"\n設定を wordpress_taxonomy.conf に保存しました")

if __name__ == "__main__":
    main()