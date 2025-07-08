#!/usr/bin/env python3
"""
現在の分析結果をブログとXに投稿
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.blog_publisher import BlogPublisher
from src.blog_analyzer import BlogAnalyzer
from src.chart_generator import ChartGenerator
import logging
from src.logger import setup_logger

# ログ設定
logger = setup_logger(__name__, level=logging.INFO)

def publish_current_analysis():
    """現在の分析結果を投稿"""
    
    logger.info("=== 現在時刻の分析投稿開始 ===")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')}")
    
    try:
        # 1. チャート生成
        logger.info("チャートを生成中...")
        generator = ChartGenerator('USDJPY=X')
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        
        screenshots = generator.generate_multiple_charts(
            timeframes=['5min', '1hour'],
            output_dir=screenshot_dir,
            candle_count=288
        )
        logger.info(f"チャート生成完了: {list(screenshots.keys())}")
        
        # 2. ブログ用分析生成
        logger.info("ブログ用分析を生成中...")
        blog_analyzer = BlogAnalyzer()
        blog_analysis = blog_analyzer.analyze_for_blog(screenshots)
        logger.info(f"分析生成完了: {len(blog_analysis)}文字")
        
        # 分析内容のプレビュー
        print("\n" + "="*60)
        print("分析内容プレビュー（最初の300文字）:")
        print("="*60)
        print(blog_analysis[:300] + "...")
        print("="*60 + "\n")
        
        # 3. WordPress + X 投稿
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
        
        logger.info("WordPressとXに投稿中...")
        publisher = BlogPublisher(wordpress_config, twitter_config)
        results = publisher.publish_analysis(blog_analysis, screenshots)
        
        # 結果表示
        print("\n" + "="*60)
        print("投稿結果:")
        print("="*60)
        
        if results['wordpress_url']:
            print(f"✅ WordPress投稿成功:")
            print(f"   URL: {results['wordpress_url']}")
        else:
            print("❌ WordPress投稿失敗")
            
        if results['twitter_url']:
            print(f"\n✅ X投稿成功:")
            print(f"   URL: {results['twitter_url']}")
        else:
            print("\n❌ X投稿失敗")
            
        print("="*60)
        
        # 成功メッセージ
        if results['wordpress_url'] and results['twitter_url']:
            print("\n🎉 両方への投稿が成功しました！")
            print(f"📊 生成されたチャート: {screenshot_dir}/")
            print(f"📝 投稿時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')}")
        
        return results
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"\n❌ エラー: {e}")
        return None

if __name__ == "__main__":
    # 実行確認
    print("現在の分析結果をWordPressとXに投稿します。")
    print("これは本番投稿です。続行しますか？")
    
    # 自動実行（確認なし）
    print("\n⚠️  自動実行モードで投稿を開始します...\n")
    
    results = publish_current_analysis()
    
    if results:
        print("\n✅ 投稿処理が完了しました")
    else:
        print("\n❌ 投稿処理に失敗しました")