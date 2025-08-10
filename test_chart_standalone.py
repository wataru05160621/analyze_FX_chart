#!/usr/bin/env python3
"""Standalone test of chart generation."""

import io
from datetime import datetime, timedelta
import random

# Try to import required modules
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import mplfinance as mpf
    print("✓ All required modules imported successfully")
except ImportError as e:
    print(f"✗ Missing module: {e}")
    print("\nPlease install required packages:")
    print("pip3 install --break-system-packages pandas matplotlib mplfinance")
    exit(1)

def create_sample_data():
    """Create sample OHLCV data for testing."""
    # Generate 200 data points
    base_price = 155.000
    now = datetime.now()
    
    data = []
    for i in range(200):
        timestamp = now - timedelta(minutes=5 * (199 - i))
        
        # Generate random price movement
        random.seed(42 + i)  # Reproducible randomness
        
        open_price = base_price + random.uniform(-0.5, 0.5)
        close_price = open_price + random.uniform(-0.2, 0.2)
        high_price = max(open_price, close_price) + random.uniform(0, 0.1)
        low_price = min(open_price, close_price) - random.uniform(0, 0.1)
        volume = random.randint(1000, 5000)
        
        data.append({
            'datetime': timestamp,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
        
        # Update base price for next candle
        base_price = close_price
    
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    
    return df

def calculate_ema(df, period):
    """Calculate Exponential Moving Average."""
    return df['close'].ewm(span=period, adjust=False).mean()

def generate_chart(df, timeframe="5m", pair="USDJPY"):
    """Generate a professional FX chart as PNG bytes."""
    
    if df.empty:
        print("Empty dataframe")
        return None
    
    # Check columns
    print(f"DataFrame columns: {df.columns.tolist()}")
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"✗ Missing required columns: {missing}")
        return None
    
    print("✓ All required columns present")
    
    # Prepare data
    df_plot = df.copy()
    
    # Calculate EMAs
    df_plot['ema25'] = calculate_ema(df_plot, 25)
    df_plot['ema100'] = calculate_ema(df_plot, 100)
    df_plot['ema200'] = calculate_ema(df_plot, 200)
    
    print(f"✓ EMAs calculated")
    
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
    
    print(f"✓ {len(additional_plots)} additional plots prepared")
    
    # Create title with timeframe
    title = f"{pair} - {timeframe}"
    
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
            'axes.spines.left': False,
            'axes.spines.right': True,
            'ytick.labelright': True,
            'ytick.labelleft': False,
            'ytick.right': True,
            'ytick.left': False
        }
    )
    
    print("✓ Style configured")
    
    # Create figure with NO VOLUME
    try:
        fig, axes = mpf.plot(
            df_plot,
            type='candle',
            style=s,
            title=title,
            ylabel='',
            volume=False,  # DISABLE VOLUME
            addplot=additional_plots if additional_plots else None,
            figsize=(12, 6),
            returnfig=True,
            datetime_format='%m/%d %H:%M',
            xrotation=0,
            tight_layout=True,
            scale_padding={'left': 0.05, 'right': 0.15, 'top': 0.1, 'bottom': 0.05}
        )
        print("✓ Chart created")
    except Exception as e:
        print(f"✗ Error creating chart: {e}")
        import traceback
        traceback.print_exc()
        return None
    
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
    
    print(f"✓ Chart generated, size: {len(chart_bytes)} bytes")
    
    return chart_bytes

def main():
    """Test chart generation."""
    print("Creating sample data...")
    df = create_sample_data()
    
    print(f"DataFrame shape: {df.shape}")
    print(f"Index type: {type(df.index)}")
    print(f"First timestamp: {df.index[0]}")
    print(f"Last timestamp: {df.index[-1]}")
    
    print("\nGenerating chart...")
    chart_bytes = generate_chart(df)
    
    if chart_bytes:
        # Save chart to file
        output_file = "test_chart_standalone.png"
        with open(output_file, 'wb') as f:
            f.write(chart_bytes)
        
        print(f"\n✓ Chart saved to {output_file}")
    else:
        print("\n✗ Failed to generate chart")

if __name__ == "__main__":
    main()