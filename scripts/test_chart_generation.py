#!/usr/bin/env python
"""Test the updated chart generation with new styling."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.charting.mpl import ChartGenerator
from src.data_fetcher.twelvedata import TwelveDataClient
from src.utils.config import config

def test_chart_generation():
    """Test chart generation with real or sample data."""
    
    print("🎨 Testing Chart Generation with New Styling")
    print("=" * 60)
    
    # Initialize components
    fetcher = TwelveDataClient()
    generator = ChartGenerator()
    
    # Try to fetch real data first
    print("\n📊 Fetching market data...")
    try:
        data = fetcher.fetch_multi_timeframe(["5m", "1h"])
        
        if data and all(not df.empty for df in data.values()):
            print("✅ Using real market data")
        else:
            print("⚠️ No real data available, using sample data")
            data = generate_sample_data()
    except Exception as e:
        print(f"⚠️ Failed to fetch real data: {e}")
        print("Using sample data instead")
        data = generate_sample_data()
    
    # Generate sample analysis for annotations
    sample_analysis = {
        "timeframes": {
            "5m": {
                "indicators": {
                    "current_price": data["5m"]["close"].iloc[-1],
                    "ema25_slope_deg": -15.5,
                    "atr20": 0.08,
                    "spread": 0.1,
                    "build_up": {
                        "width_pips": 12.3,
                        "bars": 15
                    }
                },
                "setup": "Pullback"
            },
            "1h": {
                "indicators": {
                    "current_price": data["1h"]["close"].iloc[-1],
                    "ema25_slope_deg": 22.3,
                    "atr20": 0.25,
                    "spread": 0.1,
                    "build_up": {
                        "width_pips": 45.2,
                        "bars": 8
                    }
                },
                "setup": "Pattern Break"
            }
        }
    }
    
    # Generate charts
    print("\n🖼️ Generating charts...")
    charts = generator.generate_multi_timeframe_charts(data, sample_analysis)
    
    # Save charts
    output_dir = "test_charts"
    os.makedirs(output_dir, exist_ok=True)
    
    for timeframe, chart_bytes in charts.items():
        filename = f"{output_dir}/test_{timeframe}_chart.png"
        with open(filename, "wb") as f:
            f.write(chart_bytes)
        print(f"✅ Saved {timeframe} chart to {filename}")
        print(f"   Size: {len(chart_bytes):,} bytes")
    
    print("\n" + "=" * 60)
    print("✅ Chart generation test completed!")
    print(f"📁 Charts saved in '{output_dir}' directory")
    print("\n📋 Chart Features Implemented:")
    print("  • Dark theme background (#0a0e27)")
    print("  • Cyan/Red candlesticks")
    print("  • EMA25 (white), EMA100 (yellow), EMA200 (red)")
    print("  • Current price line and label")
    print("  • Grid lines with low opacity")
    print("  • Timeframe in title")
    print("  • Indicator annotations box")
    print("  • EMA legend")
    
    return True

def generate_sample_data():
    """Generate sample OHLCV data for testing."""
    # Generate 5m data
    now = datetime.now()
    dates_5m = pd.date_range(end=now, periods=200, freq='5min')
    
    # Generate realistic price movements
    np.random.seed(42)
    base_price = 147.5
    prices_5m = base_price + np.cumsum(np.random.randn(200) * 0.02)
    
    df_5m = pd.DataFrame({
        'open': prices_5m + np.random.randn(200) * 0.01,
        'high': prices_5m + np.abs(np.random.randn(200) * 0.02),
        'low': prices_5m - np.abs(np.random.randn(200) * 0.02),
        'close': prices_5m,
        'volume': np.random.randint(100, 1000, 200)
    }, index=dates_5m)
    
    # Ensure OHLC relationship
    df_5m['high'] = df_5m[['open', 'high', 'close']].max(axis=1)
    df_5m['low'] = df_5m[['open', 'low', 'close']].min(axis=1)
    
    # Generate 1h data
    dates_1h = pd.date_range(end=now, periods=200, freq='1h')
    prices_1h = base_price + np.cumsum(np.random.randn(200) * 0.05)
    
    df_1h = pd.DataFrame({
        'open': prices_1h + np.random.randn(200) * 0.02,
        'high': prices_1h + np.abs(np.random.randn(200) * 0.04),
        'low': prices_1h - np.abs(np.random.randn(200) * 0.04),
        'close': prices_1h,
        'volume': np.random.randint(500, 5000, 200)
    }, index=dates_1h)
    
    # Ensure OHLC relationship
    df_1h['high'] = df_1h[['open', 'high', 'close']].max(axis=1)
    df_1h['low'] = df_1h[['open', 'low', 'close']].min(axis=1)
    
    return {"5m": df_5m, "1h": df_1h}

if __name__ == "__main__":
    try:
        success = test_chart_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)