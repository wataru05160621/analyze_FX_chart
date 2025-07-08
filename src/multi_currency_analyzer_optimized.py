"""
複数通貨ペアの分析を実行するモジュール（レート制限対応版）
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from .chart_generator import ChartGenerator
from .claude_analyzer import ClaudeAnalyzer
from .notion_writer import NotionWriter
from .logger import setup_logger
from .error_handler import handle_error, AnalysisError

logger = setup_logger(__name__)

# 分析対象の通貨ペア設定
CURRENCY_PAIRS = {
    'USD/JPY': {
        'symbol': 'USDJPY=X',
        'name': 'ドル円',
        'description': '米ドル/日本円'
    },
    'XAU/USD': {
        'symbol': 'GC=F',  # Gold futures
        'name': 'ゴールド',
        'description': '金/米ドル'
    },
    'BTC/USD': {
        'symbol': 'BTC-USD',
        'name': 'ビットコイン',
        'description': 'ビットコイン/米ドル'
    }
}

class MultiCurrencyAnalyzerOptimized:
    """複数通貨ペアを分析するクラス（レート制限対応）"""
    
    def __init__(self):
        self.claude_analyzer = ClaudeAnalyzer()
        self.notion_writer = NotionWriter()
        self.results = {}
        
    async def analyze_currency_pair(self, pair_name: str, pair_config: Dict) -> Dict:
        """単一通貨ペアの分析を実行"""
        try:
            logger.info(f"{pair_name}の分析を開始...")
            
            # 1. チャート生成
            generator = ChartGenerator(pair_config['symbol'])
            screenshot_dir = Path("screenshots") / pair_name.replace('/', '_')
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            screenshots = generator.generate_multiple_charts(
                timeframes=['5min', '1hour'],
                output_dir=screenshot_dir,
                candle_count=288
            )
            logger.info(f"{pair_name}: チャート生成完了")
            
            # 2. AI分析
            analysis_result = self.claude_analyzer.analyze_charts(screenshots)
            logger.info(f"{pair_name}: AI分析完了 ({len(analysis_result)}文字)")
            
            # 3. 結果を保存
            result = {
                'pair_name': pair_name,
                'pair_config': pair_config,
                'screenshots': screenshots,
                'analysis': analysis_result,
                'timestamp': datetime.now(),
                'status': 'success'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"{pair_name}の分析でエラー: {e}")
            return {
                'pair_name': pair_name,
                'pair_config': pair_config,
                'error': str(e),
                'timestamp': datetime.now(),
                'status': 'error'
            }
    
    async def analyze_all_pairs_sequential(self) -> Dict:
        """すべての通貨ペアを順次分析（レート制限対応）"""
        logger.info(f"複数通貨ペア分析開始（順次実行）: {list(CURRENCY_PAIRS.keys())}")
        
        analysis_results = {}
        
        for pair_name, pair_config in CURRENCY_PAIRS.items():
            # 各分析の間に遅延を入れる（レート制限対策）
            if analysis_results:  # 2つ目以降の分析の場合
                logger.info("レート制限対策のため30秒待機中...")
                await asyncio.sleep(30)
            
            result = await self.analyze_currency_pair(pair_name, pair_config)
            analysis_results[pair_name] = result
            
            # 分析成功後、即座にNotionに保存
            if result.get('status') == 'success':
                try:
                    self.save_single_to_notion(pair_name, result)
                except Exception as e:
                    logger.error(f"{pair_name}: Notion保存エラー: {e}")
        
        return analysis_results
    
    def save_single_to_notion(self, pair_name: str, result: Dict):
        """単一の分析結果をNotionに保存"""
        if result.get('status') == 'success':
            try:
                # タイトルに通貨ペア名を含める
                title = f"{result['pair_config']['name']}分析_{datetime.now().strftime('%Y%m%d_%H%M')}"
                
                # 分析結果に通貨ペア情報を追加
                enhanced_analysis = f"""# {result['pair_config']['description']} ({pair_name})

{result['analysis']}

---
分析時刻: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S JST')}
"""
                
                # Notionに保存（通貨ペアを指定）
                page_id = self.notion_writer.create_analysis_page(
                    title=title,
                    analysis=enhanced_analysis,
                    chart_images=result['screenshots'],
                    currency=pair_name
                )
                
                logger.info(f"{pair_name}: Notionページ作成完了 (ID: {page_id})")
                
            except Exception as e:
                logger.error(f"{pair_name}: Notion保存エラー: {e}")
    
    def save_to_notion(self, analysis_results: Dict):
        """分析結果をNotionに保存（既存メソッドとの互換性のため）"""
        for pair_name, result in analysis_results.items():
            if result.get('status') == 'success':
                self.save_single_to_notion(pair_name, result)
            else:
                logger.warning(f"{pair_name}: エラーのためNotion保存をスキップ")
    
    def generate_summary_report(self, analysis_results: Dict) -> str:
        """全通貨ペアのサマリーレポートを生成"""
        report = f"""# 複数通貨ペア分析サマリー
        
実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')}

## 分析結果概要

"""
        success_count = 0
        error_count = 0
        
        for pair_name, result in analysis_results.items():
            if result.get('status') == 'success':
                success_count += 1
                report += f"✅ **{pair_name}**: 分析完了\n"
            else:
                error_count += 1
                report += f"❌ **{pair_name}**: エラー ({result.get('error', 'Unknown error')})\n"
        
        report += f"""
        
## 統計
- 成功: {success_count}件
- エラー: {error_count}件
- 合計: {len(analysis_results)}件
"""
        
        return report


async def run_multi_currency_analysis_optimized():
    """複数通貨ペアの分析を実行するメイン関数（レート制限対応）"""
    try:
        logger.info("=== 複数通貨ペア分析開始（レート制限対応版）===")
        
        analyzer = MultiCurrencyAnalyzerOptimized()
        
        # すべての通貨ペアを順次分析
        results = await analyzer.analyze_all_pairs_sequential()
        
        # サマリーレポート生成
        summary = analyzer.generate_summary_report(results)
        logger.info(f"\n{summary}")
        
        # サマリーをファイルに保存
        summary_path = Path("analysis_summary.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"サマリーレポートを保存: {summary_path}")
        
        return results
        
    except Exception as e:
        logger.error(f"複数通貨ペア分析でエラー: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # スタンドアロン実行
    asyncio.run(run_multi_currency_analysis_optimized())