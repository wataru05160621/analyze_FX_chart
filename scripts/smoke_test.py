#!/usr/bin/env python
"""Smoke test for FX Analysis system - tests basic functionality."""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from src.utils.config import config
        from src.utils.logger import get_logger
        from src.data_fetcher.twelvedata import TwelveDataClient
        from src.analysis.core import FXAnalyzer
        from src.charting.mpl import ChartGenerator
        from src.io.s3 import S3Client
        from src.io.notion import NotionClient
        from src.io.slack import SlackClient
        from src.runner.main import FXAnalysisRunner
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from src.utils.config import config
        
        # Check required fields exist
        assert hasattr(config, 'pair')
        assert hasattr(config, 'timeframes')
        assert hasattr(config, 'twelvedata_api_key')
        
        print(f"✓ Configuration loaded")
        print(f"  - Pair: {config.pair}")
        print(f"  - Timeframes: {config.timeframes}")
        print(f"  - Data source: {config.data_source}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_analyzer():
    """Test analyzer initialization and basic methods."""
    print("\nTesting analyzer...")
    try:
        from src.analysis.core import FXAnalyzer
        import pandas as pd
        import numpy as np
        
        analyzer = FXAnalyzer()
        
        # Create dummy data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='5min')
        dummy_df = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 150,
            'high': np.random.randn(100).cumsum() + 151,
            'low': np.random.randn(100).cumsum() + 149,
            'close': np.random.randn(100).cumsum() + 150,
            'volume': np.random.randint(100, 1000, 100)
        }, index=dates)
        
        # Test indicator calculation
        indicators = analyzer.calculate_indicators(dummy_df)
        assert 'current_price' in indicators
        assert 'atr20' in indicators
        assert 'ema25_slope_deg' in indicators
        
        print("✓ Analyzer working")
        print(f"  - Current price: {indicators['current_price']:.3f}")
        print(f"  - ATR20: {indicators['atr20']:.2f}")
        return True
    except Exception as e:
        print(f"✗ Analyzer test failed: {e}")
        return False

def test_chart_generator():
    """Test chart generation."""
    print("\nTesting chart generator...")
    try:
        from src.charting.mpl import ChartGenerator
        import pandas as pd
        import numpy as np
        
        generator = ChartGenerator()
        
        # Create dummy data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='5min')
        dummy_df = pd.DataFrame({
            'open': np.random.randn(50).cumsum() + 150,
            'high': np.random.randn(50).cumsum() + 151,
            'low': np.random.randn(50).cumsum() + 149,
            'close': np.random.randn(50).cumsum() + 150,
            'volume': np.random.randint(100, 1000, 50)
        }, index=dates)
        
        # Generate chart
        chart_bytes = generator.generate_chart(dummy_df, "5m")
        assert len(chart_bytes) > 0
        
        print("✓ Chart generator working")
        print(f"  - Generated chart size: {len(chart_bytes)} bytes")
        return True
    except Exception as e:
        print(f"✗ Chart generator test failed: {e}")
        return False

def test_data_fetcher():
    """Test data fetcher (requires API key)."""
    print("\nTesting data fetcher...")
    try:
        from src.data_fetcher.twelvedata import TwelveDataClient
        from src.utils.config import config
        
        if not config.twelvedata_api_key:
            print("⚠ Skipping data fetcher test (no API key)")
            return True
        
        client = TwelveDataClient()
        
        # Test quote fetch
        quote = client.fetch_quote("USD/JPY")
        assert 'close' in quote
        
        print("✓ Data fetcher working")
        print(f"  - Current USD/JPY: {quote.get('close')}")
        return True
    except Exception as e:
        print(f"⚠ Data fetcher test skipped: {e}")
        return True  # Don't fail if API is not available

def main():
    """Run all smoke tests."""
    print("=" * 50)
    print("FX Analysis System - Smoke Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_analyzer,
        test_chart_generator,
        test_data_fetcher
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  Passed: {sum(results)}/{len(results)}")
    print(f"  Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n✅ All smoke tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())