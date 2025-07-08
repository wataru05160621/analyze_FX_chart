"""
複数通貨ペアの分析を実行するモジュール
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

class MultiCurrencyAnalyzer:
    """複数通貨ペアを分析するクラス"""
    
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
    
    async def analyze_all_pairs(self) -> Dict:
        """すべての通貨ペアを並行して分析"""
        logger.info(f"複数通貨ペア分析開始: {list(CURRENCY_PAIRS.keys())}")
        
        # 並行実行のためのタスクを作成
        tasks = []
        for pair_name, pair_config in CURRENCY_PAIRS.items():
            task = self.analyze_currency_pair(pair_name, pair_config)
            tasks.append(task)
        
        # すべてのタスクを並行実行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を整理
        analysis_results = {}
        for i, (pair_name, _) in enumerate(CURRENCY_PAIRS.items()):
            if isinstance(results[i], Exception):
                logger.error(f"{pair_name}で例外発生: {results[i]}")
                analysis_results[pair_name] = {
                    'status': 'error',
                    'error': str(results[i])
                }
            else:
                analysis_results[pair_name] = results[i]
        
        return analysis_results
    
    def save_to_notion(self, analysis_results: Dict):
        """分析結果をNotionに保存"""
        for pair_name, result in analysis_results.items():
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


async def run_multi_currency_analysis():
    """複数通貨ペアの分析を実行するメイン関数"""
    try:
        logger.info("=== 複数通貨ペア分析開始 ===")
        
        analyzer = MultiCurrencyAnalyzer()
        
        # すべての通貨ペアを分析
        results = await analyzer.analyze_all_pairs()
        
        # Notionに保存
        analyzer.save_to_notion(results)
        
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
    asyncio.run(run_multi_currency_analysis())