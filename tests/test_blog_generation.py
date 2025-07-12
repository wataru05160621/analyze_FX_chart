#!/usr/bin/env python3
"""
ブログ用分析のテスト生成スクリプト
"""
import asyncio
import sys
from pathlib import Path
import logging

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.chart_generator import ChartGenerator
from src.blog_analyzer import BlogAnalyzer
from src.logger import setup_logger

# ログ設定
logger = setup_logger(__name__, level=logging.INFO)

async def test_blog_generation():
    """ブログ用分析のテスト生成"""
    try:
        logger.info("テスト開始: ブログ用分析生成")
        
        # 1. チャート生成
        logger.info("チャートを生成中...")
        generator = ChartGenerator('USDJPY=X')
        
        # スクリーンショットディレクトリ作成
        screenshot_dir = Path("test_screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        
        # 複数時間足のチャート生成
        screenshots = generator.generate_multiple_charts(
            timeframes=['5min', '1hour'],
            output_dir=screenshot_dir,
            candle_count=288
        )
        
        logger.info(f"チャート生成完了: {screenshots}")
        
        # 2. ブログ用分析生成
        logger.info("ブログ用分析を生成中...")
        blog_analyzer = BlogAnalyzer()
        blog_analysis = blog_analyzer.analyze_for_blog(screenshots)
        
        # 3. 結果を保存
        output_file = Path("test_blog_analysis.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(blog_analysis)
        
        logger.info(f"ブログ用分析を保存しました: {output_file}")
        
        # 4. 結果の一部を表示
        print("\n" + "="*50)
        print("ブログ用分析結果（最初の1000文字）:")
        print("="*50 + "\n")
        print(blog_analysis[:1000] + "...\n")
        
        # 5. 重要な特徴をチェック
        print("="*50)
        print("内容チェック:")
        print("="*50)
        
        checks = {
            "免責事項（文頭）": "投資助言ではありません" in blog_analysis[:500],
            "売買非推奨": all(word not in blog_analysis or "売買は自己判断" in blog_analysis 
                          for word in ["買いエントリー", "売りエントリー", "利確", "損切り"]),
            "教育的内容": "書籍" in blog_analysis and "学習" in blog_analysis,
            "ビルドアップ分析": "ビルドアップ" in blog_analysis,
            "EMA解説": "EMA" in blog_analysis or "指数移動平均" in blog_analysis,
            "免責事項（文末）": "投資助言ではありません" in blog_analysis[-500:],
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        print(f"\n✅ テスト完了: ブログ用分析が正常に生成されました")
        print(f"📄 完全な分析結果: {output_file}")
        print(f"📊 生成されたチャート: {screenshot_dir}/")
        
        return True
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # デバッグモード設定
    if "--debug" in sys.argv:
        setup_logger(__name__, level=logging.DEBUG)
    
    # テスト実行
    success = asyncio.run(test_blog_generation())
    
    if not success:
        print("\n❌ テストが失敗しました")
        sys.exit(1)