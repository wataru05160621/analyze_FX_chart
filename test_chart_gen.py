#!/usr/bin/env python3
"""Test chart generation with sample data."""

import os
import sys
import json
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set env vars
os.environ['PAIR'] = 'USDJPY'
os.environ['SYMBOL'] = 'USD/JPY'
os.environ['TIMEFRAMES'] = '5m,1h'
os.environ['LOG_LEVEL'] = 'DEBUG'

from src.charting.mpl import ChartGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)

def create_sample_data():
    """Create sample OHLCV data for testing."""
    # Generate 200 data points
    base_price = 155.000
    now = datetime.now()
    
    data = []
    for i in range(200):
        timestamp = now - timedelta(minutes=5 * (199 - i))
        
        # Generate random price movement
        import random
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

def main():
    """Test chart generation."""
    print("Creating sample data...")
    df = create_sample_data()
    
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"First few rows:")
    print(df.head())
    
    print("\nGenerating chart...")
    generator = ChartGenerator(pair="USDJPY")
    
    try:
        chart_bytes = generator.generate_chart(df, "5m")
        
        # Save chart to file
        output_file = "test_chart.png"
        with open(output_file, 'wb') as f:
            f.write(chart_bytes)
        
        print(f"Chart saved to {output_file}")
        print(f"Chart size: {len(chart_bytes)} bytes")
        
    except Exception as e:
        print(f"Error generating chart: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()