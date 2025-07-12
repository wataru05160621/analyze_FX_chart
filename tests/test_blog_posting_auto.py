#!/usr/bin/env python3
"""
WordPress + X 連携自動テストスクリプト（確認なし）
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.blog_publisher import BlogPublisher
from src.blog_analyzer import BlogAnalyzer
from src.chart_generator import ChartGenerator

def test_blog_posting_auto():
    """ブログ投稿の自動テスト"""
    
    # 設定確認
    print("=== 設定確認 ===")
    print(f"WordPress URL: {os.getenv('WORDPRESS_URL')}")
    print(f"WordPress Username: {os.getenv('WORDPRESS_USERNAME')}")
    print(f"Twitter API Key: {os.getenv('TWITTER_API_KEY')[:10]}...")
    print()
    
    # 1. テストチャート生成
    print("=== チャート生成 ===")
    generator = ChartGenerator('USDJPY=X')
    screenshot_dir = Path("test_screenshots")
    screenshot_dir.mkdir(exist_ok=True)
    
    screenshots = generator.generate_multiple_charts(
        timeframes=['5min', '1hour'],
        output_dir=screenshot_dir,
        candle_count=288
    )
    print(f"チャート生成完了: {screenshots}")
    print()
    
    # 2. ブログ用分析生成
    print("=== ブログ用分析生成 ===")
    blog_analyzer = BlogAnalyzer()
    blog_analysis = blog_analyzer.analyze_for_blog(screenshots)
    print(f"分析生成完了: {len(blog_analysis)}文字")
    print()
    
    # 分析内容の一部を表示
    print("=== 分析内容（最初の500文字）===")
    print(blog_analysis[:500] + "...")
    print()
    
    # 3. WordPress + X 投稿テスト
    wordpress_config = {
        "url": os.getenv("WORDPRESS_URL"),
        "username": os.getenv("WORDPRESS_USERNAME"),
        "password": os.getenv("WORDPRESS_PASSWORD")
    }
    
    twitter_config = {
        "api_key": os.getenv("TWITTER_API_KEY"),
        "api_secret": os.getenv("TWITTER_API_SECRET"),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    }
    
    print("\n=== 投稿実行 ===")
    print("⚠️  テスト投稿を実行します...")
    publisher = BlogPublisher(wordpress_config, twitter_config)
    
    try:
        results = publisher.publish_analysis(blog_analysis, screenshots)
        
        print("\n=== 投稿結果 ===")
        if results['wordpress_url']:
            print(f"✅ WordPress投稿成功: {results['wordpress_url']}")
        else:
            print("❌ WordPress投稿失敗")
            
        if results['twitter_url']:
            print(f"✅ X投稿成功: {results['twitter_url']}")
        else:
            print("❌ X投稿失敗")
            
        print("\n⚠️  注意: テスト投稿のため、必要に応じて削除してください")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blog_posting_auto()