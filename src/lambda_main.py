"""
FXチャート分析メインモジュール（Lambda軽量版）
チャート生成は省略し、既存の画像または外部APIを使用
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List
from src.config import (
    ANALYSIS_MODE,
    NOTION_DATABASE_ID
)
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.error_handler import handle_error, ErrorRecorder, AnalysisError
from src.logger import setup_logger

# ロガーのセットアップ
logger = setup_logger(__name__)

def _validate_configuration():
    """設定の検証"""
    errors = []
    
    # Claude API設定チェック
    if ANALYSIS_MODE == "claude":
        from src.config import CLAUDE_API_KEY
        if not CLAUDE_API_KEY or CLAUDE_API_KEY == "your_claude_api_key_here":
            errors.append("CLAUDE_API_KEYが設定されていません")
    
    # Notion設定チェック
    from src.config import NOTION_API_KEY, NOTION_DATABASE_ID
    if not NOTION_API_KEY:
        errors.append("NOTION_API_KEYが設定されていません")
    if not NOTION_DATABASE_ID:
        errors.append("NOTION_DATABASE_IDが設定されていません")
    
    if errors:
        error_msg = "設定エラー:\n" + "\n".join(errors)
        raise ValueError(error_msg)

async def analyze_fx_charts() -> Dict:
    """
    FXチャート分析を実行（Lambda軽量版）
    
    Returns:
        Dict: 分析結果
    """
    start_time = datetime.now()
    logger.info(f"FXチャート分析開始: {start_time}")
    
    try:
        # 設定検証
        _validate_configuration()
        
        # Lambda環境用の一時ディレクトリ設定
        screenshots_dir = "/tmp/screenshots"
        try:
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
        except Exception as e:
            logger.warning(f"ディレクトリ作成スキップ: {e}")
            
        # チャート画像がない場合はダミー画像情報を作成
        screenshots = {
            "5min": {"path": "no_chart_5min.png", "size": 0},
            "1hour": {"path": "no_chart_1hour.png", "size": 0}
        }
        
        logger.info(f"チャート画像情報: {screenshots}")
        
        # 分析実行
        if ANALYSIS_MODE == "claude":
            analyzer = ClaudeAnalyzer()
            logger.info("Claude分析器を使用")
        else:
            raise ValueError(f"Lambda環境では {ANALYSIS_MODE} はサポートされていません")
        
        # テキストベースの分析（チャート画像なしのデモ）
        analysis_text = await _perform_text_analysis(analyzer)
        
        # Notion書き込み
        notion_writer = NotionWriter()
        
        # ページデータ準備
        page_data = {
            "title": f"FX分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "timestamp": datetime.now().isoformat(),
            "timeframe": "5min,1hour",
            "analysis": analysis_text,
            "status": "成功",
            "environment": "Lambda",
            "screenshots_count": 0,
            "execution_time": str(datetime.now() - start_time)
        }
        
        # Lambda版では画像をアップロードしないのでダミーパスを使用
        notion_page_id = notion_writer.create_analysis_page(
            title=page_data["title"],
            analysis=page_data["analysis"],
            chart_images={}  # 空の辞書を渡す
        )
        logger.info(f"Notionページ作成完了: {notion_page_id}")
        
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        result = {
            "status": "success",
            "timestamp": end_time.isoformat(),
            "execution_time_seconds": execution_time.total_seconds(),
            "screenshots": screenshots,
            "analysis": analysis_text,
            "notion_page_id": notion_page_id,
            "environment": "lambda"
        }
        
        logger.info(f"分析完了: {execution_time.total_seconds():.2f}秒")
        return result
        
    except Exception as e:
        error_msg = f"分析処理でエラーが発生: {str(e)}"
        logger.error(error_msg)
        logger.error(f"エラー詳細", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": (datetime.now() - start_time).total_seconds()
        }

async def _perform_text_analysis(analyzer) -> str:
    """
    テキストベースの分析を実行
    """
    # サンプル市場データ（実際は外部APIから取得）
    market_context = """
    USD/JPY市場概況:
    - 現在価格: 158.25円
    - 24時間変動: +0.45円 (+0.28%)
    - 日足高値: 158.50円
    - 日足安値: 157.80円
    - RSI: 65.2 (やや買われ過ぎ)
    - MACD: 上昇トレンド継続
    - 25MA: 157.90円 (上向き)
    - 75MA: 157.20円 (上向き)
    - 200MA: 156.10円 (上向き)
    
    市場ニュース:
    - 日銀の金融政策決定会合を控え、円安圧力が継続
    - 米国雇用統計は予想を上回る結果
    - 地政学的リスクによる安全資産需要は限定的
    """
    
    try:
        analysis = await analyzer.analyze_text(market_context)
        return analysis
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        return f"分析でエラーが発生しました: {str(e)}"

if __name__ == "__main__":
    asyncio.run(analyze_fx_charts())