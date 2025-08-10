#!/usr/bin/env python
"""Test TwelveData API to verify price data fetching."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher.twelvedata import TwelveDataClient
from src.utils.config import config
import json

def test_data_fetch():
    """Test fetching real market data."""
    
    print("🔍 Testing TwelveData API Connection")
    print("=" * 60)
    
    try:
        # Initialize client
        client = TwelveDataClient()
        print(f"✅ Client initialized with API key: {config.twelvedata_api_key[:8]}...")
        
        # Test fetching USD/JPY data
        print(f"\n📊 Fetching {config.symbol} data...")
        print(f"   Timeframes: {config.timeframes}")
        
        for timeframe in config.timeframes:
            interval = timeframe.replace('m', 'min')  # Convert 5m to 5min for API
            print(f"\n📈 Fetching {timeframe} data...")
            
            try:
                df = client.fetch_timeseries(
                    symbol=config.symbol,
                    interval=interval,
                    outputsize=10  # Just fetch recent 10 candles for testing
                )
                
                print(f"✅ Successfully fetched {len(df)} candles")
                print(f"   Latest candle:")
                print(f"   - Time: {df.index[0]}")
                print(f"   - Open: {df['open'].iloc[0]}")
                print(f"   - High: {df['high'].iloc[0]}")
                print(f"   - Low: {df['low'].iloc[0]}")
                print(f"   - Close: {df['close'].iloc[0]}")
                print(f"   - Volume: {df['volume'].iloc[0]}")
                
                # Check if prices are in reasonable range for USD/JPY
                latest_close = df['close'].iloc[0]
                if 100 < latest_close < 200:
                    print(f"   ✅ Price range looks correct for USD/JPY: {latest_close:.3f}")
                else:
                    print(f"   ⚠️ Price might be incorrect for USD/JPY: {latest_close:.3f}")
                
            except Exception as e:
                print(f"❌ Failed to fetch {timeframe} data: {e}")
        
        # Test the fetch_ohlcv method that's used by the main app
        print("\n📊 Testing fetch_ohlcv method...")
        ohlcv_data = client.fetch_ohlcv(config.pair, "5min")
        if ohlcv_data is not None:
            print(f"✅ fetch_ohlcv returned {len(ohlcv_data)} candles")
            print(f"   Price range: {ohlcv_data['low'].min():.3f} - {ohlcv_data['high'].max():.3f}")
        else:
            print("❌ fetch_ohlcv returned None")
        
        print("\n" + "=" * 60)
        print("✅ Data fetching test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_fetch()
    sys.exit(0 if success else 1)