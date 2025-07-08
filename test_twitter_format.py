#!/usr/bin/env python3
"""
X（Twitter）投稿フォーマットのテスト
"""
from datetime import datetime
from src.blog_publisher import BlogPublisher

# ダミーの分析結果
dummy_analysis = """
# プライスアクションの原則に基づくUSD/JPYチャート解説

## 1. 現在のチャート状況

### 基本情報
- 通貨ペア: USD/JPY
- 現在価格: 143.10円前後

### EMAの配置
- 25EMA > 75EMA > 200EMA（上昇配列）

### ビルドアップの観察
- 教科書的な完璧な形状のビルドアップを形成

### パターン認識
- 三角保ち合いパターンの形成
"""

# BlogPublisherのインスタンス作成（ダミー設定）
publisher = BlogPublisher(
    wordpress_config={"url": "", "username": "", "password": ""},
    twitter_config={"api_key": "", "api_secret": "", "access_token": "", "access_token_secret": ""}
)

# Twitter要約の生成
summary = publisher.extract_summary_for_twitter(dummy_analysis)

# ブログURLを含めた投稿例
blog_url = "https://example.com/2025/01/01/usdjpy-analysis"
tweet_with_url = f"{summary}\n\n詳細分析はこちら👇\n{blog_url}"

print("="*60)
print("X（Twitter）投稿フォーマット例")
print("="*60)
print("\n【要約部分のみ】")
print(f"文字数: {len(summary)}文字")
print("-"*60)
print(summary)
print("-"*60)

print("\n【ブログURL付き】")
print(f"文字数: {len(tweet_with_url)}文字")
print("-"*60)
print(tweet_with_url)
print("-"*60)

# 文字数チェック
if len(tweet_with_url) <= 280:
    print("\n✅ 280文字以内に収まっています")
else:
    print(f"\n❌ 文字数オーバー: {len(tweet_with_url) - 280}文字超過")