"""
MT4トレード自動記録システム
MetaTrader4のレポートファイルを監視して自動的にトレードを記録
"""
import os
import time
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
from bs4 import BeautifulSoup

from phase1_data_collector import Phase1DataCollector, TradeRecord
from chart_generator import ChartGenerator
from claude_analyzer import ClaudeAnalyzer

logger = logging.getLogger(__name__)

class MT4ReportWatcher(FileSystemEventHandler):
    """MT4のレポートファイルを監視するクラス"""
    
    def __init__(self, mt4_files_path: str, collector: Phase1DataCollector):
        self.mt4_files_path = Path(mt4_files_path)
        self.collector = collector
        self.processed_trades = self._load_processed_trades()
        self.chart_generator = ChartGenerator('USDJPY=X')
        self.analyzer = ClaudeAnalyzer()
        
    def _load_processed_trades(self) -> set:
        """処理済みトレードIDを読み込み"""
        processed_file = Path('phase1_data/processed_trades.json')
        if processed_file.exists():
            with open(processed_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_processed_trades(self):
        """処理済みトレードIDを保存"""
        processed_file = Path('phase1_data/processed_trades.json')
        processed_file.parent.mkdir(exist_ok=True)
        with open(processed_file, 'w') as f:
            json.dump(list(self.processed_trades), f)
    
    def on_modified(self, event):
        """ファイル変更を検知"""
        if event.is_directory:
            return
            
        # MT4のレポートファイルかチェック
        if event.src_path.endswith('.htm') or event.src_path.endswith('.html'):
            logger.info(f"MT4レポート検出: {event.src_path}")
            self.process_mt4_report(event.src_path)
    
    def process_mt4_report(self, report_path: str):
        """MT4レポートを解析してトレードを記録"""
        try:
            # レポートを解析
            trades = self.parse_mt4_report(report_path)
            
            # 新規トレードのみ処理
            for trade in trades:
                trade_id = f"MT4_{trade['ticket']}"
                if trade_id not in self.processed_trades:
                    self.record_trade(trade)
                    self.processed_trades.add(trade_id)
            
            self._save_processed_trades()
            
        except Exception as e:
            logger.error(f"レポート処理エラー: {e}")
    
    def parse_mt4_report(self, report_path: str) -> List[Dict]:
        """MT4のHTMLレポートを解析"""
        trades = []
        
        try:
            with open(report_path, 'r', encoding='utf-16') as f:
                content = f.read()
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(content, 'html.parser')
            
            # トレード履歴テーブルを探す
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 13:  # MT4レポートの標準列数
                    try:
                        # トレード情報を抽出
                        trade_data = {
                            'ticket': cells[0].text.strip(),
                            'open_time': cells[1].text.strip(),
                            'type': cells[2].text.strip(),
                            'lots': cells[3].text.strip(),
                            'symbol': cells[4].text.strip(),
                            'price': cells[5].text.strip(),
                            'sl': cells[6].text.strip(),
                            'tp': cells[7].text.strip(),
                            'close_time': cells[8].text.strip(),
                            'close_price': cells[9].text.strip(),
                            'commission': cells[10].text.strip(),
                            'swap': cells[11].text.strip(),
                            'profit': cells[12].text.strip()
                        }
                        
                        # 決済済みトレードのみ
                        if trade_data['close_time'] and trade_data['close_time'] != '':
                            trades.append(trade_data)
                            
                    except Exception as e:
                        continue
            
            return trades
            
        except Exception as e:
            logger.error(f"レポート解析エラー: {e}")
            return []
    
    def record_trade(self, trade_data: Dict):
        """トレードを自動記録"""
        try:
            # トレード時のチャートを生成
            entry_chart, exit_chart = self.generate_trade_charts(
                trade_data['open_time'],
                trade_data['close_time']
            )
            
            # AI分析を実行
            ai_analysis = self.analyze_trade_setup(
                entry_chart,
                trade_data
            )
            
            # セットアップタイプを推定
            setup_type = self.estimate_setup_type(
                trade_data,
                ai_analysis
            )
            
            # TradeRecordを作成
            trade_record = TradeRecord(
                trade_id=f"MT4_{trade_data['ticket']}",
                timestamp=datetime.now().isoformat(),
                session=self.determine_session(trade_data['open_time']),
                setup_type=setup_type,
                entry_price=float(trade_data['price']),
                entry_time=self.convert_mt4_time(trade_data['open_time']),
                signal_quality=ai_analysis.get('quality_score', 3),
                buildup_duration=ai_analysis.get('buildup_duration', 0),
                buildup_pattern=ai_analysis.get('buildup_pattern', 'Unknown'),
                ema_configuration=ai_analysis.get('ema_config', 'Unknown'),
                atr_at_entry=ai_analysis.get('atr', 7.0),
                spread_at_entry=self.estimate_spread(trade_data),
                volatility_level=ai_analysis.get('volatility', 'Medium'),
                news_nearby=False,  # TODO: ニュースカレンダー連携
                exit_price=float(trade_data['close_price']),
                exit_time=self.convert_mt4_time(trade_data['close_time']),
                exit_reason=self.determine_exit_reason(trade_data),
                pips_result=self.calculate_pips(trade_data),
                profit_loss=float(trade_data['profit']),
                max_favorable_excursion=ai_analysis.get('mfe', 0),
                max_adverse_excursion=ai_analysis.get('mae', 0),
                time_in_trade=self.calculate_duration(trade_data),
                entry_chart_path=str(entry_chart),
                exit_chart_path=str(exit_chart),
                ai_analysis_summary=ai_analysis.get('summary', ''),
                confidence_score=ai_analysis.get('confidence', 0.5)
            )
            
            # データベースに保存
            self.collector.save_trade(trade_record)
            logger.info(f"トレード自動記録完了: {trade_record.trade_id}")
            
            # Slackに通知
            self.notify_trade_recorded(trade_record)
            
        except Exception as e:
            logger.error(f"トレード記録エラー: {e}")
    
    def generate_trade_charts(self, open_time: str, close_time: str) -> tuple:
        """トレード時のチャートを生成"""
        try:
            charts_dir = Path('phase1_data/trade_charts')
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            # エントリー時のチャート生成
            entry_timestamp = self.convert_mt4_time(open_time)
            entry_chart = charts_dir / f"entry_{entry_timestamp.replace(':', '')}.png"
            
            # エグジット時のチャート生成
            exit_timestamp = self.convert_mt4_time(close_time)
            exit_chart = charts_dir / f"exit_{exit_timestamp.replace(':', '')}.png"
            
            # TODO: 実際のチャート生成
            # self.chart_generator.generate_chart_at_time(entry_timestamp, entry_chart)
            # self.chart_generator.generate_chart_at_time(exit_timestamp, exit_chart)
            
            return entry_chart, exit_chart
            
        except Exception as e:
            logger.error(f"チャート生成エラー: {e}")
            return None, None
    
    def analyze_trade_setup(self, chart_path: Path, trade_data: Dict) -> Dict:
        """AIでトレードセットアップを分析"""
        try:
            # TODO: Claude APIでチャート分析
            # analysis = self.analyzer.analyze_charts({'5min': chart_path})
            
            # 仮の分析結果
            return {
                'quality_score': 4,
                'buildup_duration': 45,
                'buildup_pattern': '三角保ち合い',
                'ema_config': '上昇配列',
                'atr': 8.5,
                'volatility': 'Medium',
                'mfe': 25.0,
                'mae': -5.0,
                'summary': 'パターンブレイクからのエントリー',
                'confidence': 0.75
            }
            
        except Exception as e:
            logger.error(f"AI分析エラー: {e}")
            return {}
    
    def estimate_setup_type(self, trade_data: Dict, ai_analysis: Dict) -> str:
        """セットアップタイプを推定"""
        # コメントから推定
        comment = trade_data.get('comment', '').upper()
        if 'PATTERN_BREAK' in comment or 'SETUP_A' in comment:
            return 'A'
        elif 'PULLBACK' in comment or 'SETUP_B' in comment:
            return 'B'
        
        # AI分析から推定
        summary = ai_analysis.get('summary', '')
        if 'パターンブレイク' in summary:
            return 'A'
        elif 'プルバック' in summary:
            return 'B'
        
        return 'Unknown'
    
    def determine_session(self, mt4_time: str) -> str:
        """セッションを判定"""
        try:
            dt = datetime.strptime(mt4_time, '%Y.%m.%d %H:%M')
            hour = dt.hour
            
            if 7 <= hour < 15:
                return "アジア"
            elif 15 <= hour < 21:
                return "ロンドン"
            else:
                return "NY"
        except:
            return "Unknown"
    
    def convert_mt4_time(self, mt4_time: str) -> str:
        """MT4時刻形式を変換"""
        try:
            dt = datetime.strptime(mt4_time, '%Y.%m.%d %H:%M')
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    def estimate_spread(self, trade_data: Dict) -> float:
        """スプレッドを推定"""
        # TODO: 実際の市場データから取得
        return 1.2
    
    def determine_exit_reason(self, trade_data: Dict) -> str:
        """終了理由を判定"""
        profit = float(trade_data['profit'])
        tp = float(trade_data['tp']) if trade_data['tp'] else 0
        sl = float(trade_data['sl']) if trade_data['sl'] else 0
        close_price = float(trade_data['close_price'])
        
        if tp > 0 and abs(close_price - tp) < 0.01:
            return 'TP'
        elif sl > 0 and abs(close_price - sl) < 0.01:
            return 'SL'
        else:
            return '手動'
    
    def calculate_pips(self, trade_data: Dict) -> float:
        """pips計算"""
        entry = float(trade_data['price'])
        exit = float(trade_data['close_price'])
        
        if trade_data['type'] == 'buy':
            pips = (exit - entry) * 100
        else:
            pips = (entry - exit) * 100
        
        return round(pips, 1)
    
    def calculate_duration(self, trade_data: Dict) -> int:
        """トレード時間を計算（分）"""
        try:
            open_dt = datetime.strptime(trade_data['open_time'], '%Y.%m.%d %H:%M')
            close_dt = datetime.strptime(trade_data['close_time'], '%Y.%m.%d %H:%M')
            duration = (close_dt - open_dt).total_seconds() / 60
            return int(duration)
        except:
            return 0
    
    def notify_trade_recorded(self, trade: TradeRecord):
        """Slackに記録通知"""
        try:
            import requests
            webhook = os.environ.get('SLACK_WEBHOOK_URL')
            
            if webhook:
                message = {
                    'text': f'*トレード自動記録完了*\n'
                           f'ID: {trade.trade_id}\n'
                           f'結果: {trade.pips_result} pips\n'
                           f'セットアップ: {trade.setup_type}\n'
                           f'品質スコア: {trade.signal_quality}/5'
                }
                requests.post(webhook, json=message)
                
        except Exception as e:
            logger.error(f"通知エラー: {e}")

def start_mt4_watcher():
    """MT4監視を開始"""
    # MT4のFilesフォルダパス（環境に応じて変更）
    mt4_paths = [
        'C:/Users/[Username]/AppData/Roaming/MetaQuotes/Terminal/[ID]/MQL4/Files',
        '/Users/[Username]/Library/Application Support/MetaTrader 4/[ID]/MQL4/Files'
    ]
    
    # 実際のパスを探す
    mt4_path = None
    for path in mt4_paths:
        if os.path.exists(path):
            mt4_path = path
            break
    
    if not mt4_path:
        logger.error("MT4パスが見つかりません")
        return
    
    # 監視開始
    collector = Phase1DataCollector()
    event_handler = MT4ReportWatcher(mt4_path, collector)
    observer = Observer()
    observer.schedule(event_handler, mt4_path, recursive=False)
    observer.start()
    
    logger.info(f"MT4監視開始: {mt4_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    start_mt4_watcher()