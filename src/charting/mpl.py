"""Chart generation using matplotlib with professional styling."""

import io
from datetime import datetime
from typing import Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import mplfinance as mpf
import pandas as pd
import numpy as np
import pytz

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ChartGenerator:
    """Generate FX charts using matplotlib/mplfinance with professional styling."""
    
    def __init__(self, pair: str = None):
        """Initialize chart generator."""
        self.pair = pair or config.pair
        self.jst = pytz.timezone("Asia/Tokyo")
        
        # Set dark theme
        plt.style.use('dark_background')
        
    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return df['close'].ewm(span=period, adjust=False).mean()
        
    def generate_chart(
        self,
        df: pd.DataFrame,
        timeframe: str,
        indicators: Optional[Dict] = None,
        setup: Optional[str] = None
    ) -> bytes:
        """
        Generate a professional FX chart as PNG bytes.
        
        Args:
            df: OHLCV DataFrame with datetime index
            timeframe: Timeframe label (e.g., "5m", "1h")
            indicators: Optional indicators to plot
            setup: Optional setup type to annotate
            
        Returns:
            PNG image as bytes
        """
        if df.empty:
            logger.warning(f"Empty dataframe for {timeframe} chart")
            return self._generate_empty_chart(timeframe)
        
        # Prepare data
        df_plot = df.copy()
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df_plot.columns for col in required_cols):
            logger.error(f"Missing required columns for chart: {df_plot.columns.tolist()}")
            return self._generate_empty_chart(timeframe)
        
        # Calculate EMAs
        df_plot['ema25'] = self.calculate_ema(df_plot, 25)
        df_plot['ema100'] = self.calculate_ema(df_plot, 100)
        df_plot['ema200'] = self.calculate_ema(df_plot, 200)
        
        # Create additional plots for EMAs
        additional_plots = []
        
        # EMA25 - White
        if len(df_plot) >= 25:
            additional_plots.append(mpf.make_addplot(
                df_plot['ema25'],
                color='white',
                width=1.5,
                alpha=0.9
            ))
        
        # EMA100 - Yellow
        if len(df_plot) >= 100:
            additional_plots.append(mpf.make_addplot(
                df_plot['ema100'],
                color='yellow',
                width=1.5,
                alpha=0.9
            ))
        
        # EMA200 - Red
        if len(df_plot) >= 200:
            additional_plots.append(mpf.make_addplot(
                df_plot['ema200'],
                color='#FF5252',
                width=1.5,
                alpha=0.9
            ))
        
        # Add current price line
        current_price = df_plot['close'].iloc[-1]
        current_price_line = [current_price] * len(df_plot)
        additional_plots.append(mpf.make_addplot(
            pd.Series(current_price_line, index=df_plot.index),
            color='white',
            linestyle='--',
            width=1,
            alpha=0.5
        ))
        
        # Create title with timeframe
        title = f"{self.pair} - {timeframe}"
        
        # Define custom market colors for dark theme
        mc = mpf.make_marketcolors(
            up='#00E5FF',  # Cyan for bullish
            down='#FF5252',  # Red for bearish
            edge='inherit',
            wick={'up': '#00E5FF', 'down': '#FF5252'},
            volume='inherit',
            alpha=0.9
        )
        
        # Create custom style with dark background
        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='--',
            gridcolor='#333333',
            gridaxis='both',
            facecolor='#0a0e27',  # Dark navy background
            edgecolor='white',
            figcolor='#0a0e27',
            rc={
                'axes.labelcolor': 'white',
                'axes.edgecolor': '#333333',
                'xtick.color': 'white',
                'ytick.color': 'white',
                'grid.alpha': 0.2,
                'font.size': 10,
                'axes.titlesize': 12,
                'axes.titleweight': 'bold',
                'axes.titlecolor': 'white',
                'axes.spines.left': False,  # Hide left spine
                'axes.spines.right': True,  # Show right spine
                'ytick.labelright': True,   # Labels on right
                'ytick.labelleft': False,   # No labels on left
                'ytick.right': True,         # Ticks on right
                'ytick.left': False          # No ticks on left
            }
        )
        
        # Create figure with NO VOLUME
        fig, axes = mpf.plot(
            df_plot,
            type='candle',
            style=s,
            title=title,
            ylabel='',  # Remove ylabel since it will be on the right
            volume=False,  # DISABLE VOLUME
            addplot=additional_plots if additional_plots else None,
            figsize=(12, 6),
            returnfig=True,
            datetime_format='%m/%d %H:%M',
            xrotation=0,
            tight_layout=True,
            scale_padding={'left': 0.05, 'right': 0.15, 'top': 0.1, 'bottom': 0.05}
        )
        
        # Get the main price axis
        ax_price = axes[0]
        
        # Move y-axis to right side
        ax_price.yaxis.tick_right()
        ax_price.yaxis.set_label_position('right')
        ax_price.set_ylabel('Price', rotation=270, labelpad=20, color='white')
        
        # Hide left spine, show right spine
        ax_price.spines['left'].set_visible(False)
        ax_price.spines['right'].set_visible(True)
        ax_price.spines['right'].set_color('#333333')
        
        # Add current price label on the right
        self._add_current_price_label(ax_price, current_price, df_plot)
        
        # Add EMA legend
        self._add_ema_legend(ax_price, df_plot)
        
        # Add additional annotations if indicators provided
        if indicators:
            self._add_indicator_annotations(ax_price, df_plot, indicators)
        
        # Fine-tune grid appearance
        ax_price.grid(True, linestyle='--', linewidth=0.5, alpha=0.2)
        ax_price.set_facecolor('#0a0e27')
        
        # Adjust text colors
        ax_price.tick_params(axis='y', colors='white', labelright=True, labelleft=False)
        ax_price.tick_params(axis='x', colors='white')
        
        # Convert to bytes
        buf = io.BytesIO()
        fig.savefig(
            buf, 
            format='png', 
            dpi=100, 
            bbox_inches='tight',
            facecolor='#0a0e27',
            edgecolor='none'
        )
        buf.seek(0)
        chart_bytes = buf.read()
        
        # Close figure to free memory
        plt.close(fig)
        
        logger.info(f"Generated {timeframe} chart, size: {len(chart_bytes)} bytes")
        
        return chart_bytes
    
    def _add_current_price_label(self, ax, current_price, df):
        """Add current price label on the right side of the chart."""
        # Get the last candle color
        last_close = df['close'].iloc[-1]
        last_open = df['open'].iloc[-1]
        is_bullish = last_close >= last_open
        label_color = '#00E5FF' if is_bullish else '#FF5252'
        
        # Add price label as text annotation on the right
        ax.annotate(
            f'{current_price:.3f}',
            xy=(1.01, current_price),
            xycoords=('axes fraction', 'data'),
            ha='left',
            va='center',
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor=label_color,
                edgecolor='none',
                alpha=0.8
            ),
            color='white',
            fontsize=9,
            fontweight='bold'
        )
    
    def _add_ema_legend(self, ax, df):
        """Add EMA legend to the chart."""
        legend_elements = []
        
        if len(df) >= 25:
            legend_elements.append(mpatches.Patch(color='white', label='EMA25'))
        if len(df) >= 100:
            legend_elements.append(mpatches.Patch(color='yellow', label='EMA100'))
        if len(df) >= 200:
            legend_elements.append(mpatches.Patch(color='#FF5252', label='EMA200'))
        
        if legend_elements:
            ax.legend(
                handles=legend_elements,
                loc='upper left',
                frameon=True,
                facecolor='#0a0e27',
                edgecolor='#333333',
                labelcolor='white',
                fontsize=8,
                framealpha=0.9
            )
    
    def _add_indicator_annotations(self, ax, df, indicators):
        """Add indicator information to the chart."""
        info_text = []
        
        if 'ema25_slope_deg' in indicators:
            slope = indicators['ema25_slope_deg']
            info_text.append(f"EMA25 Slope: {slope:.1f}°")
        
        if 'atr20' in indicators:
            info_text.append(f"ATR20: {indicators['atr20']:.1f}p")
        
        if 'spread' in indicators:
            info_text.append(f"Spread: {indicators['spread']:.1f}p")
        
        if 'build_up' in indicators:
            bu = indicators['build_up']
            if bu.get('width_pips', 0) > 0:
                info_text.append(f"Build-up: {bu['width_pips']:.1f}p × {bu['bars']} bars")
        
        # Place info box in top right (but not overlapping with price axis)
        if info_text:
            text = '\n'.join(info_text)
            ax.text(
                0.95, 0.98,
                text,
                transform=ax.transAxes,
                fontsize=8,
                ha='right',
                va='top',
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='#0a0e27',
                    edgecolor='#333333',
                    alpha=0.9
                ),
                color='white'
            )
    
    def _generate_empty_chart(self, timeframe: str) -> bytes:
        """Generate an empty chart with message."""
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='#0a0e27')
        ax.set_facecolor('#0a0e27')
        
        ax.text(
            0.5, 0.5,
            f"No data available for {timeframe}",
            transform=ax.transAxes,
            fontsize=20,
            horizontalalignment='center',
            verticalalignment='center',
            color='white'
        )
        ax.set_title(f"{self.pair} - {timeframe}", color='white', fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_color('#333333')
        ax.spines['bottom'].set_color('#333333')
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_color('#333333')
        
        buf = io.BytesIO()
        fig.savefig(
            buf, 
            format='png', 
            dpi=100, 
            bbox_inches='tight',
            facecolor='#0a0e27',
            edgecolor='none'
        )
        buf.seek(0)
        chart_bytes = buf.read()
        
        plt.close(fig)
        
        return chart_bytes
    
    def generate_multi_timeframe_charts(
        self,
        data: Dict[str, pd.DataFrame],
        analysis: Optional[Dict] = None
    ) -> Dict[str, bytes]:
        """
        Generate charts for multiple timeframes.
        
        Args:
            data: Dict mapping timeframe to DataFrame
            analysis: Optional analysis results
            
        Returns:
            Dict mapping timeframe to PNG bytes
        """
        charts = {}
        
        for timeframe, df in data.items():
            indicators = None
            setup = None
            
            if analysis and "timeframes" in analysis:
                if timeframe in analysis["timeframes"]:
                    tf_analysis = analysis["timeframes"][timeframe]
                    indicators = tf_analysis.get("indicators")
                    setup = tf_analysis.get("setup")
            
            try:
                chart_bytes = self.generate_chart(df, timeframe, indicators, setup)
                charts[timeframe] = chart_bytes
                logger.info(f"Generated chart for {timeframe}")
            except Exception as e:
                logger.error(f"Failed to generate chart for {timeframe}", error=str(e))
                charts[timeframe] = self._generate_empty_chart(timeframe)
        
        return charts