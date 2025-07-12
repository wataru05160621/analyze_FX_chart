"""
ハイブリッド型FX分析システム
定額制サービスとAPIを組み合わせてコストを最適化
"""
import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai
from anthropic import Anthropic

from .logger import setup_logger
from .chart_generator import ChartGenerator
from .notion_writer import NotionWriter
from .config import CLAUDE_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID

logger = setup_logger(__name__)

class HybridAnalyzer:
    """定額制と従量制を組み合わせた分析システム"""
    
    def __init__(self):
        # Google Gemini（無料枠：60クエリ/分）
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Claude API（バックアップ用）
        self.claude_client = Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None
        
        # Notion
        self.notion_writer = NotionWriter()
        
    async def analyze_with_gemini(self, chart_images: Dict[str, Path], currency: str) -> Optional[str]:
        """Gemini APIで分析（無料枠活用）"""
        try:
            logger.info(f"{currency}: Gemini分析開始（無料枠）")
            
            # 画像をアップロード
            images = []
            for timeframe, image_path in chart_images.items():
                image = genai.upload_file(str(image_path), mime_type="image/png")
                images.append(image)
            
            # プロンプト
            prompt = f"""
            {currency}のFXチャート分析を実施してください。
            
            【分析項目】
            1. 現在のトレンド方向と強さ
            2. 重要なサポート・レジスタンスレベル
            3. エントリーポイントの提案
            4. リスク管理（損切り・利確レベル）
            
            【注意事項】
            - プロのトレーダー向けの実践的な分析
            - 具体的な価格レベルを明記
            - リスクリワード比を考慮
            
            簡潔で実用的な分析をお願いします。
            """
            
            # 分析実行
            response = self.gemini_model.generate_content([prompt] + images)
            analysis = response.text
            
            logger.info(f"{currency}: Gemini分析完了（{len(analysis)}文字）")
            return analysis
            
        except Exception as e:
            logger.error(f"{currency}: Gemini分析エラー: {e}")
            return None
    
    async def analyze_with_claude_minimal(self, chart_images: Dict[str, Path], currency: str) -> Optional[str]:
        """Claude APIで最小限の分析（トークン節約）"""
        try:
            logger.info(f"{currency}: Claude最小分析開始")
            
            # 最も重要な1枚の画像のみ使用
            main_image = chart_images.get('1hour') or list(chart_images.values())[0]
            
            with open(main_image, "rb") as f:
                import base64
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 簡潔なプロンプト
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{currency}チャート分析：トレンド、エントリー、SL/TP（300文字以内）"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    }
                ]
            }]
            
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",  # 最も安価なモデル
                max_tokens=500,
                messages=messages
            )
            
            analysis = response.content[0].text
            logger.info(f"{currency}: Claude分析完了（{len(analysis)}文字）")
            return analysis
            
        except Exception as e:
            logger.error(f"{currency}: Claude分析エラー: {e}")
            return None
    
    async def batch_analyze_currencies(self, currencies: Dict[str, Dict]) -> Dict:
        """複数通貨をバッチ処理で分析"""
        results = {}
        
        # 優先順位を設定
        priority_currencies = ['USD/JPY']  # 高優先度
        other_currencies = [c for c in currencies if c not in priority_currencies]
        
        # 高優先度通貨はClaude APIで詳細分析
        for currency in priority_currencies:
            if currency in currencies:
                logger.info(f"{currency}: 高優先度分析開始")
                
                # チャート生成
                generator = ChartGenerator(currencies[currency]['symbol'])
                screenshots = generator.generate_multiple_charts(
                    timeframes=['5min', '1hour'],
                    output_dir=Path("screenshots") / currency.replace('/', '_')
                )
                
                # Claude APIで分析
                analysis = await self.analyze_with_claude_minimal(screenshots, currency)
                
                if analysis:
                    results[currency] = {
                        'status': 'success',
                        'analysis': analysis,
                        'screenshots': screenshots,
                        'analyzer': 'claude'
                    }
        
        # その他の通貨はGemini無料枠で分析
        for currency in other_currencies:
            logger.info(f"{currency}: 通常分析開始")
            
            # チャート生成
            generator = ChartGenerator(currencies[currency]['symbol'])
            screenshots = generator.generate_multiple_charts(
                timeframes=['5min', '1hour'],
                output_dir=Path("screenshots") / currency.replace('/', '_')
            )
            
            # Gemini APIで分析
            analysis = await self.analyze_with_gemini(screenshots, currency)
            
            if analysis:
                results[currency] = {
                    'status': 'success',
                    'analysis': analysis,
                    'screenshots': screenshots,
                    'analyzer': 'gemini'
                }
            else:
                # Gemini失敗時はClaudeでバックアップ
                analysis = await self.analyze_with_claude_minimal(screenshots, currency)
                if analysis:
                    results[currency] = {
                        'status': 'success',
                        'analysis': analysis,
                        'screenshots': screenshots,
                        'analyzer': 'claude_backup'
                    }
            
            # レート制限対策（Gemini: 60回/分）
            await asyncio.sleep(1)
        
        return results
    
    def save_results_to_notion(self, results: Dict):
        """分析結果をNotionに保存"""
        for currency, result in results.items():
            if result.get('status') == 'success':
                try:
                    title = f"{currency}分析_{datetime.now().strftime('%Y%m%d_%H%M')}"
                    
                    # アナライザー情報を追加
                    enhanced_analysis = f"""{result['analysis']}

---
分析エンジン: {result['analyzer']}
分析時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')}
"""
                    
                    page_id = self.notion_writer.create_analysis_page(
                        title=title,
                        analysis=enhanced_analysis,
                        chart_images=result['screenshots'],
                        currency=currency
                    )
                    
                    logger.info(f"{currency}: Notionページ作成完了 (ID: {page_id})")
                    
                except Exception as e:
                    logger.error(f"{currency}: Notion保存エラー: {e}")


# 実行例
async def run_hybrid_analysis():
    """ハイブリッド分析の実行"""
    
    currencies = {
        'USD/JPY': {'symbol': 'USDJPY=X', 'name': 'ドル円'},
        'XAU/USD': {'symbol': 'GC=F', 'name': 'ゴールド'},
        'BTC/USD': {'symbol': 'BTC-USD', 'name': 'ビットコイン'}
    }
    
    analyzer = HybridAnalyzer()
    
    # バッチ分析実行
    results = await analyzer.batch_analyze_currencies(currencies)
    
    # Notionに保存
    analyzer.save_results_to_notion(results)
    
    # コスト概算
    claude_count = sum(1 for r in results.values() if 'claude' in r.get('analyzer', ''))
    gemini_count = sum(1 for r in results.values() if r.get('analyzer') == 'gemini')
    
    logger.info(f"""
=== 分析完了 ===
Claude API使用: {claude_count}回
Gemini API使用: {gemini_count}回（無料枠）
推定月額コスト: ${claude_count * 0.01 * 150:.2f}
""")

if __name__ == "__main__":
    asyncio.run(run_hybrid_analysis())