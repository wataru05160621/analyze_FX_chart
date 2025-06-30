"""
Pythonでチャートを生成するモジュール（SMA付き）
"""
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Tuple, Optional
import mplfinance as mpf
import numpy as np

logger = logging.getLogger(__name__)

class ChartGenerator:
    """yfinanceとmatplotlibを使用してSMA付きチャートを生成"""
    
    def __init__(self, symbol: str = "USDJPY=X"):
        """
        Args:
            symbol: Yahoo Finance形式のシンボル（例: USDJPY=X）
        """
        self.symbol = symbol
        
    def fetch_data(self, period: str = "1mo", interval: str = "5m") -> pd.DataFrame:
        """
        価格データを取得
        
        Args:
            period: データ期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
            interval: 時間足（1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo）
        """
        try:
            ticker = yf.Ticker(self.symbol)
            
            # intervalに応じてperiodを調整
            if interval in ['1m', '2m', '5m', '15m', '30m']:
                # 分足の場合は短期間のデータのみ取得可能
                if period not in ['1d', '5d', '1mo']:
                    period = '5d'
            
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                raise ValueError(f"データが取得できませんでした: {self.symbol}")
                
            logger.info(f"データ取得成功: {len(data)}本のローソク足")
            return data
            
        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            raise
            
    def calculate_sma(self, data: pd.DataFrame, periods: list = [25, 75, 200]) -> pd.DataFrame:
        """
        SMAを計算
        
        Args:
            data: 価格データ
            periods: SMAの期間リスト
        """
        for period in periods:
            if len(data) >= period:
                data[f'SMA{period}'] = data['Close'].rolling(window=period).mean()
                logger.info(f"SMA{period}を計算しました（データ数: {len(data)}本）")
            else:
                logger.warning(f"データ不足: SMA{period}の計算には{period}本以上のデータが必要です（現在: {len(data)}本）")
                # データが不足している場合でも、利用可能な分で計算
                data[f'SMA{period}'] = data['Close'].rolling(window=min(period, len(data))).mean()
                
        return data
        
    def generate_chart(self, 
                      timeframe: str = "5min",
                      output_dir: Path = None,
                      periods: list = [25, 75, 200],
                      candle_count: int = 288) -> Path:
        """
        SMA付きチャートを生成
        
        Args:
            timeframe: 時間足（5min, 15min, 30min, 1hour, 4hour, 1day）
            output_dir: 出力ディレクトリ
            periods: SMAの期間
            
        Returns:
            生成されたチャート画像のパス
        """
        # 時間足マッピング
        interval_map = {
            "5min": "5m",
            "15min": "15m", 
            "30min": "30m",
            "1hour": "60m",
            "4hour": "1d",  # 4時間足は日足で代用
            "1day": "1d"
        }
        
        # 期間マッピング（288本+200本SMA用データ=488本以上取得するために十分な期間を設定）
        period_map = {
            "5m": "5d",      # 5日間で約1440本（平日のみ）
            "15m": "7d",     # 7日間で約672本
            "30m": "7d",     # 7日間で約336本  
            "60m": "1mo",    # 1ヶ月で約720本
            "1d": "2y"       # 2年間で約730本
        }
        
        interval = interval_map.get(timeframe, "5m")
        period = period_map.get(interval, "1mo")
        
        try:
            # データ取得（SMA計算のため余分にデータを取得）
            max_sma_period = max(periods) if periods else 200
            required_data_count = candle_count + max_sma_period
            
            data = self.fetch_data(period=period, interval=interval)
            logger.info(f"取得データ数: {len(data)}本")
            
            # SMA計算（すべてのデータで計算）
            data = self.calculate_sma(data, periods)
            
            # 表示用に指定された本数のローソク足のみを使用（SMAは正しく計算済み）
            if len(data) > candle_count:
                # 最新のcandle_count本のみを表示用に切り出し
                data = data.tail(candle_count)
                logger.info(f"表示用データを最新{candle_count}本に制限しました（SMAは{len(data) + max_sma_period}本で計算済み）")
            
            # チャート生成
            if output_dir is None:
                output_dir = Path("screenshots")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"chart_{timeframe}_{timestamp}.png"
            
            # mplfinanceスタイル設定
            mc = mpf.make_marketcolors(
                up='tab:green',
                down='tab:red',
                edge='inherit',
                wick={'up':'green', 'down':'red'},
                volume='inherit'
            )
            
            style = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle=':',
                y_on_right=True,
                figcolor='#1e1e1e',
                facecolor='#1e1e1e',
                edgecolor='#3a3a3a',
                gridcolor='#3a3a3a',
                gridaxis='both'
            )
            
            # SMAプロット設定
            added_plots = []
            colors = ['gold', 'red', 'darkred']
            
            for i, period in enumerate(periods):
                if f'SMA{period}' in data.columns:
                    added_plots.append(
                        mpf.make_addplot(
                            data[f'SMA{period}'],
                            color=colors[i % len(colors)],
                            width=2,
                            label=f'SMA{period}'
                        )
                    )
            
            # フィギュアサイズを計算（ローソク足が見やすくなるように）
            # 288本のローソク足に対して適切な幅を設定
            width = max(16, candle_count * 0.08)  # 最小16インチ、1本あたり0.08インチ
            height = 8
            
            # チャート描画
            fig, axes = mpf.plot(
                data,
                type='candle',
                style=style,
                addplot=added_plots if added_plots else None,
                figsize=(width, height),
                title=f'{self.symbol} - {timeframe} ({len(data)} candles)',
                ylabel='Price',
                ylabel_lower='',
                volume=False,
                returnfig=True,
                datetime_format='%m/%d %H:%M' if interval in ['5m', '15m', '30m', '60m'] else '%Y/%m/%d',
                xrotation=45,
                tight_layout=True,
                warn_too_much_data=500  # 警告を抑制
            )
            
            # 価格軸（Y軸）の目盛りを0.100円刻みに設定
            ax = axes[0]
            y_min, y_max = ax.get_ylim()
            # 0.1刻みの目盛りを生成
            y_ticks = np.arange(np.floor(y_min * 10) / 10, np.ceil(y_max * 10) / 10 + 0.1, 0.1)
            ax.set_yticks(y_ticks)
            ax.set_yticklabels([f'{y:.3f}' for y in y_ticks])
            
            # 時間軸（X軸）の目盛りを調整
            # X軸の範囲を取得
            x_min, x_max = ax.get_xlim()
            
            if timeframe == "5min":
                # 5分足は1時間ごと（約12本のローソク足ごと）
                # 表示する目盛りの数を制限
                num_ticks = int((x_max - x_min) / 12)  # 12本 = 1時間
                num_ticks = max(5, min(num_ticks, 24))  # 5〜24個の目盛り
                x_tick_positions = np.linspace(x_min, x_max, num_ticks)
                ax.set_xticks(x_tick_positions)
            elif timeframe == "1hour":
                # 1時間足は12時間ごと
                num_ticks = int((x_max - x_min) / 12)  # 12本 = 12時間
                num_ticks = max(3, min(num_ticks, 10))  # 3〜10個の目盛り
                x_tick_positions = np.linspace(x_min, x_max, num_ticks)
                ax.set_xticks(x_tick_positions)
            
            # グリッドラインを更新
            ax.grid(True, which='both', alpha=0.3)
            
            # 凡例追加
            if added_plots:
                lines = []
                labels = []
                for i, period in enumerate(periods):
                    if f'SMA{period}' in data.columns:
                        line, = ax.plot([], [], color=colors[i % len(colors)], linewidth=2)
                        lines.append(line)
                        labels.append(f'SMA{period}')
                ax.legend(lines, labels, loc='upper left')
            
            # 保存
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1e1e1e')
            plt.close()
            
            logger.info(f"チャート生成完了: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"チャート生成エラー: {e}")
            raise
            
    def generate_multiple_charts(self, 
                               timeframes: list = ["5min", "1hour"],
                               output_dir: Path = None,
                               candle_count: int = 288) -> dict:
        """
        複数の時間足でチャートを生成
        
        Args:
            timeframes: 時間足のリスト
            output_dir: 出力ディレクトリ
            
        Returns:
            {時間足: 画像パス}の辞書
        """
        charts = {}
        
        for timeframe in timeframes:
            try:
                path = self.generate_chart(timeframe, output_dir, candle_count=candle_count)
                charts[timeframe] = path
            except Exception as e:
                logger.error(f"{timeframe}チャート生成失敗: {e}")
                
        return charts