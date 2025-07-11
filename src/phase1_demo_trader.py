"""
Phase1 デモトレード自動実行システム
Volmanセットアップを検出して自動的にデモトレードを実行・記録
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import random
from pathlib import Path

from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.phase1_data_collector import Phase1DataCollector, TradeRecord

logger = logging.getLogger(__name__)

class Phase1DemoTrader:
    """自動デモトレードシステム"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator('USDJPY=X')
        self.analyzer = ClaudeAnalyzer()
        self.collector = Phase1DataCollector()
        self.active_trades = {}
        self.is_running = False
        
    async def start_trading(self):
        """自動トレードを開始"""
        self.is_running = True
        logger.info("Phase1 デモトレード開始")
        
        while self.is_running:
            try:
                # 現在の市場分析
                setup = await self.analyze_current_market()
                
                if setup and self.should_enter_trade(setup):
                    # エントリー実行
                    trade_id = await self.enter_trade(setup)
                    if trade_id:
                        logger.info(f"新規トレード: {trade_id}")
                
                # アクティブトレードの監視
                await self.monitor_active_trades()
                
                # 5分待機（5分足ベース）
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"トレードループエラー: {e}")
                await asyncio.sleep(60)
    
    async def analyze_current_market(self) -> Optional[Dict]:
        """現在の市場を分析してセットアップを検出"""
        try:
            # 最新チャート生成
            output_dir = Path('phase1_data/analysis') / datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            screenshots = self.chart_generator.generate_multiple_charts(
                timeframes=['5min', '1hour'],
                output_dir=output_dir,
                candle_count=288
            )
            
            # Claude分析
            analysis = self.analyzer.analyze_charts(screenshots)
            
            # セットアップ情報を抽出
            setup = self._extract_setup_info(analysis, screenshots)
            
            return setup
            
        except Exception as e:
            logger.error(f"市場分析エラー: {e}")
            return None
    
    def _extract_setup_info(self, analysis: str, screenshots: Dict) -> Optional[Dict]:
        """分析からセットアップ情報を抽出"""
        setup = {
            'timestamp': datetime.now(),
            'analysis': analysis,
            'screenshots': screenshots,
            'setup_type': None,
            'entry_price': None,
            'confidence': 0,
            'signal_quality': 0
        }
        
        # セットアップタイプの検出
        if 'セットアップA' in analysis or 'パターンブレイク' in analysis:
            setup['setup_type'] = 'A'
        elif 'セットアップB' in analysis or 'プルバック' in analysis:
            setup['setup_type'] = 'B'
        
        # 品質スコアの抽出
        if '⭐⭐⭐⭐⭐' in analysis:
            setup['signal_quality'] = 5
            setup['confidence'] = 0.9
        elif '⭐⭐⭐⭐' in analysis:
            setup['signal_quality'] = 4
            setup['confidence'] = 0.75
        elif '⭐⭐⭐' in analysis:
            setup['signal_quality'] = 3
            setup['confidence'] = 0.6
        
        # エントリー価格の抽出（仮実装）
        import re
        price_match = re.search(r'エントリー[：:]\s*([\d.]+)', analysis)
        if price_match:
            setup['entry_price'] = float(price_match.group(1))
        
        return setup if setup['setup_type'] and setup['signal_quality'] >= 3 else None
    
    def should_enter_trade(self, setup: Dict) -> bool:
        """トレードすべきか判断"""
        # アクティブトレードが多すぎないか
        if len(self.active_trades) >= 2:
            return False
        
        # セッションチェック
        current_hour = datetime.now().hour
        if current_hour < 7 or current_hour > 22:  # 深夜は避ける
            return False
        
        # 品質チェック
        if setup['signal_quality'] < 3:
            return False
        
        # スキップ条件（仮実装）
        skip_conditions = self._check_skip_conditions()
        if skip_conditions:
            logger.info(f"スキップ: {skip_conditions}")
            return False
        
        return True
    
    def _check_skip_conditions(self) -> Optional[str]:
        """Volmanスキップ条件をチェック"""
        # TODO: 実際の市場データをチェック
        # - ATR < 7pips
        # - スプレッド > 2pips
        # - ニュース前後10分
        
        # 仮実装：10%の確率でスキップ
        if random.random() < 0.1:
            return "ATR不足"
        
        return None
    
    async def enter_trade(self, setup: Dict) -> Optional[str]:
        """トレードエントリー"""
        try:
            # 現在価格取得（実際にはリアルタイムデータ必要）
            current_price = setup['entry_price'] or self._get_current_price()
            
            trade_id = f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # トレード情報
            trade_info = {
                'trade_id': trade_id,
                'setup': setup,
                'entry_price': current_price,
                'entry_time': datetime.now(),
                'tp_price': current_price + 0.20,  # +20pips
                'sl_price': current_price - 0.10,  # -10pips
                'status': 'active'
            }
            
            self.active_trades[trade_id] = trade_info
            
            # エントリー記録（部分的）
            await self._record_entry(trade_info)
            
            return trade_id
            
        except Exception as e:
            logger.error(f"エントリーエラー: {e}")
            return None
    
    async def monitor_active_trades(self):
        """アクティブトレードを監視"""
        current_price = self._get_current_price()
        
        for trade_id, trade_info in list(self.active_trades.items()):
            if trade_info['status'] != 'active':
                continue
            
            # TP/SLチェック
            if current_price >= trade_info['tp_price']:
                await self.exit_trade(trade_id, current_price, 'TP')
            elif current_price <= trade_info['sl_price']:
                await self.exit_trade(trade_id, current_price, 'SL')
            else:
                # MFE/MAE更新
                self._update_excursions(trade_info, current_price)
    
    async def exit_trade(self, trade_id: str, exit_price: float, exit_reason: str):
        """トレード決済"""
        try:
            trade_info = self.active_trades[trade_id]
            trade_info['exit_price'] = exit_price
            trade_info['exit_time'] = datetime.now()
            trade_info['exit_reason'] = exit_reason
            trade_info['status'] = 'closed'
            
            # 完全なトレード記録
            await self._record_complete_trade(trade_info)
            
            # アクティブリストから削除
            del self.active_trades[trade_id]
            
            logger.info(f"トレード決済: {trade_id} - {exit_reason}")
            
        except Exception as e:
            logger.error(f"決済エラー: {e}")
    
    def _update_excursions(self, trade_info: Dict, current_price: float):
        """MFE/MAE更新"""
        pnl = current_price - trade_info['entry_price']
        
        if 'mfe' not in trade_info:
            trade_info['mfe'] = 0
        if 'mae' not in trade_info:
            trade_info['mae'] = 0
        
        trade_info['mfe'] = max(trade_info['mfe'], pnl * 100)  # pips
        trade_info['mae'] = min(trade_info['mae'], pnl * 100)  # pips
    
    async def _record_entry(self, trade_info: Dict):
        """エントリー時の部分記録"""
        # エントリー時点のスナップショット保存
        pass
    
    async def _record_complete_trade(self, trade_info: Dict):
        """完全なトレード記録"""
        try:
            # 決済時のチャート生成
            exit_dir = Path('phase1_data/trade_charts') / trade_info['trade_id']
            exit_dir.mkdir(parents=True, exist_ok=True)
            
            exit_screenshots = self.chart_generator.generate_multiple_charts(
                timeframes=['5min'],
                output_dir=exit_dir,
                candle_count=288
            )
            
            # pips計算
            pips = (trade_info['exit_price'] - trade_info['entry_price']) * 100
            
            # TradeRecord作成
            trade_record = TradeRecord(
                trade_id=trade_info['trade_id'],
                timestamp=datetime.now().isoformat(),
                session=self._determine_session(),
                setup_type=trade_info['setup']['setup_type'],
                entry_price=trade_info['entry_price'],
                entry_time=trade_info['entry_time'].isoformat(),
                signal_quality=trade_info['setup']['signal_quality'],
                buildup_duration=45,  # 仮値
                buildup_pattern=self._extract_buildup_pattern(trade_info['setup']['analysis']),
                ema_configuration=self._extract_ema_config(trade_info['setup']['analysis']),
                atr_at_entry=8.5,  # 仮値
                spread_at_entry=1.2,  # 仮値
                volatility_level='Medium',
                news_nearby=False,
                exit_price=trade_info['exit_price'],
                exit_time=trade_info['exit_time'].isoformat(),
                exit_reason=trade_info['exit_reason'],
                pips_result=round(pips, 1),
                profit_loss=pips * 100,  # 仮の金額
                max_favorable_excursion=trade_info.get('mfe', pips),
                max_adverse_excursion=trade_info.get('mae', 0),
                time_in_trade=int((trade_info['exit_time'] - trade_info['entry_time']).total_seconds() / 60),
                entry_chart_path=str(trade_info['setup']['screenshots']['5min']),
                exit_chart_path=str(exit_screenshots['5min']),
                ai_analysis_summary=trade_info['setup']['analysis'][:500],
                confidence_score=trade_info['setup']['confidence']
            )
            
            # データベースに保存
            self.collector.save_trade(trade_record)
            
            # 日次統計更新
            today = datetime.now().strftime('%Y-%m-%d')
            self.collector.calculate_daily_stats(today)
            
            # Slack通知
            await self._notify_trade_result(trade_record)
            
        except Exception as e:
            logger.error(f"トレード記録エラー: {e}")
    
    def _get_current_price(self) -> float:
        """現在価格を取得（仮実装）"""
        # TODO: 実際の価格フィードから取得
        # ここではランダムな値を返す
        base = 150.0
        return base + random.uniform(-1, 1)
    
    def _determine_session(self) -> str:
        """現在のセッションを判定"""
        hour = datetime.now().hour
        if 7 <= hour < 15:
            return "アジア"
        elif 15 <= hour < 21:
            return "ロンドン"
        else:
            return "NY"
    
    def _extract_buildup_pattern(self, analysis: str) -> str:
        """ビルドアップパターンを抽出"""
        if '三角保ち合い' in analysis:
            return '三角保ち合い'
        elif 'フラッグ' in analysis:
            return 'フラッグ'
        elif 'ペナント' in analysis:
            return 'ペナント'
        else:
            return '不明'
    
    def _extract_ema_config(self, analysis: str) -> str:
        """EMA配列を抽出"""
        if '上昇配列' in analysis or '25EMA > 75EMA > 200EMA' in analysis:
            return '上昇配列'
        elif '下降配列' in analysis or '25EMA < 75EMA < 200EMA' in analysis:
            return '下降配列'
        else:
            return '混在'
    
    async def _notify_trade_result(self, trade: TradeRecord):
        """トレード結果をSlack通知"""
        try:
            import requests
            import os
            webhook = os.environ.get('SLACK_WEBHOOK_URL')
            
            if webhook:
                emoji = '🟢' if trade.pips_result > 0 else '🔴'
                message = {
                    'text': f'{emoji} *デモトレード結果*\n'
                           f'ID: {trade.trade_id}\n'
                           f'セットアップ: {trade.setup_type}\n'
                           f'結果: {trade.pips_result} pips ({trade.exit_reason})\n'
                           f'品質: {"⭐" * trade.signal_quality}\n'
                           f'保有時間: {trade.time_in_trade}分'
                }
                requests.post(webhook, json=message)
                
        except Exception as e:
            logger.error(f"通知エラー: {e}")

async def main():
    """メイン実行"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    trader = Phase1DemoTrader()
    
    try:
        await trader.start_trading()
    except KeyboardInterrupt:
        logger.info("デモトレード停止")
        trader.is_running = False

if __name__ == "__main__":
    asyncio.run(main())