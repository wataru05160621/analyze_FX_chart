#!/usr/bin/env python3
"""
チャート生成とテスト投稿スクリプト
"""
import os
import sys
from datetime import datetime
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """チャート生成とテスト投稿のメイン処理"""
    try:
        logger.info("=== チャート生成テスト開始 ===")
        logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. チャート生成
        logger.info("チャート生成中...")
        from src.chart_generator import ChartGenerator
        
        generator = ChartGenerator('USDJPY=X')
        output_dir = Path('screenshots') / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 複数の時間枠でチャート生成
        timeframes = ['5min', '1hour', '4hour', '1day']
        screenshots = generator.generate_multiple_charts(
            timeframes=timeframes,
            output_dir=str(output_dir)
        )
        
        logger.info(f"生成されたチャート: {screenshots}")
        
        # 2. S3にアップロード
        if os.environ.get('UPLOAD_TO_S3', 'false').lower() == 'true':
            logger.info("S3にアップロード中...")
            import boto3
            s3_client = boto3.client('s3')
            bucket_name = 'fx-analyzer-charts-ecs-prod-455931011903'
            
            for timeframe, path in screenshots.items():
                s3_key = f"charts/USDJPY/{datetime.now().strftime('%Y-%m-%d')}/{timeframe}_{datetime.now().strftime('%H%M%S')}.png"
                s3_client.upload_file(
                    str(path),
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': 'image/png'}
                )
                logger.info(f"アップロード完了: {s3_key}")
        
        # 3. Claude分析
        logger.info("Claude分析実行中...")
        from src.claude_analyzer import ClaudeAnalyzer
        
        analyzer = ClaudeAnalyzer()
        analysis = analyzer.analyze_charts(screenshots)
        logger.info(f"分析完了: {len(analysis)}文字")
        
        # 分析結果を表示
        print("\n" + "="*50)
        print("分析結果:")
        print("="*50)
        print(analysis[:1000] + "..." if len(analysis) > 1000 else analysis)
        
        # 4. Notionにテスト投稿
        if os.environ.get('POST_TO_NOTION', 'false').lower() == 'true':
            logger.info("Notionに投稿中...")
            from src.notion_writer import NotionWriter
            from src.verification_tracker import get_tracker
            
            tracker = get_tracker()
            verification_day = tracker.get_verification_text()
            
            writer = NotionWriter()
            page_id = writer.create_analysis_page(
                f"【テスト】USD/JPY分析 {datetime.now().strftime('%Y-%m-%d %H:%M')} - {verification_day}",
                analysis,
                screenshots,
                "USD/JPY"
            )
            logger.info(f"Notion投稿完了: {page_id}")
            print(f"\nNotionページID: {page_id}")
        
        logger.info("=== チャート生成テスト完了 ===")
        
    except Exception as e:
        logger.error(f"エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())