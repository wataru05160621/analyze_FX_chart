"""Chart generation using matplotlib."""

import io
from datetime import datetime
from typing import Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
import pandas as pd
import pytz

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ChartGenerator:
    """Generate FX charts using matplotlib/mplfinance."""
    
    def __init__(self, pair: str = None):
        """Initialize chart generator."""
        self.pair = pair or config.pair
        self.jst = pytz.timezone("Asia/Tokyo")
        
        # Set style
        plt.style.use('dark_background')
        
    def generate_chart(
        self,
        df: pd.DataFrame,
        timeframe: str,
        indicators: Optional[Dict] = None,
        setup: Optional[str] = None
    ) -> bytes:
        """
        Generate a chart as PNG bytes.
        
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
        
        # Create additional plots
        additional_plots = []
        
        # Add EMA if present
        if 'ema25' in df_plot.columns:
            ema_plot = mpf.make_addplot(
                df_plot['ema25'],
                color='yellow',
                width=1.5,
                label='EMA25'
            )
            additional_plots.append(ema_plot)
        
        # Add ATR if present
        if 'atr20' in df_plot.columns and len(df_plot) > 0:
            atr_plot = mpf.make_addplot(
                df_plot['atr20'],
                panel=1,
                color='cyan',
                width=1,
                ylabel='ATR20',
                secondary_y=False
            )
            additional_plots.append(atr_plot)
        
        # Create title with setup info
        title = f"{self.pair} - {timeframe}"
        if setup and setup != "No-Trade":
            title += f" | Setup: {setup}"
        
        # Market colors
        mc = mpf.make_marketcolors(
            up='green',
            down='red',
            edge='inherit',
            wick={'up': 'green', 'down': 'red'},
            volume='inherit'
        )
        
        # Style
        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='-',
            gridcolor='#333333',
            base_mpf_style='nightclouds'
        )
        
        # Create figure
        fig, axes = mpf.plot(
            df_plot,
            type='candle',
            style=s,
            title=title,
            ylabel='Price',
            volume=True if 'volume' in df_plot.columns else False,
            addplot=additional_plots if additional_plots else None,
            figsize=(12, 8),
            returnfig=True,
            datetime_format='%m/%d %H:%M',
            xrotation=15
        )
        
        # Add annotations if indicators provided
        if indicators:
            self._add_annotations(fig, axes, df_plot, indicators, timeframe)
        
        # Convert to bytes
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        chart_bytes = buf.read()
        
        # Close figure to free memory
        plt.close(fig)
        
        logger.info(f"Generated {timeframe} chart, size: {len(chart_bytes)} bytes")
        
        return chart_bytes
    
    def _add_annotations(
        self,
        fig,
        axes,
        df: pd.DataFrame,
        indicators: Dict,
        timeframe: str
    ):
        """Add annotations to the chart."""
        ax = axes[0]  # Main price axis
        
        # Add info box
        info_text = []
        
        if 'current_price' in indicators:
            info_text.append(f"Price: {indicators['current_price']:.3f}")
        
        if 'ema25_slope_deg' in indicators:
            slope = indicators['ema25_slope_deg']
            info_text.append(f"EMA Slope: {slope:.1f}°")
        
        if 'atr20' in indicators:
            info_text.append(f"ATR20: {indicators['atr20']:.1f}p")
        
        if 'build_up' in indicators:
            bu = indicators['build_up']
            if bu['width_pips'] > 0:
                info_text.append(f"Build-up: {bu['width_pips']:.1f}p x {bu['bars']} bars")
        
        # Place text box
        if info_text:
            text = '\n'.join(info_text)
            ax.text(
                0.02, 0.98,
                text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.7)
            )
        
        # Mark round numbers if present
        if 'round_numbers' in indicators:
            for level in indicators['round_numbers']:
                if df['low'].min() <= level <= df['high'].max():
                    ax.axhline(
                        y=level,
                        color='orange',
                        linestyle='--',
                        linewidth=0.5,
                        alpha=0.5
                    )
                    ax.text(
                        df.index[-1], level,
                        f" {level:.2f}",
                        fontsize=8,
                        color='orange',
                        verticalalignment='center'
                    )
    
    def _generate_empty_chart(self, timeframe: str) -> bytes:
        """Generate an empty chart with message."""
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(
            0.5, 0.5,
            f"No data available for {timeframe}",
            transform=ax.transAxes,
            fontsize=20,
            horizontalalignment='center',
            verticalalignment='center'
        )
        ax.set_title(f"{self.pair} - {timeframe}")
        ax.set_xticks([])
        ax.set_yticks([])
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
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