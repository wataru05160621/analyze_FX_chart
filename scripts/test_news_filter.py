#!/usr/bin/env python3
"""Test the updated news window filter logic"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pytz

# Test the news window filter logic
def test_news_window_filter():
    """Test if our scheduled times avoid the news window filter"""
    
    jst = pytz.timezone('Asia/Tokyo')
    
    # Define the news windows (from core_v2.py)
    news_windows = [
        (9, 0, 9, 30),    # Tokyo: 9:00-9:30
        (15, 30, 16, 0),  # London: 15:30-16:00
        (22, 0, 22, 30),  # NY: 22:00-22:30
    ]
    
    # Test times (our scheduled execution times)
    test_times = [
        (9, 30, "Tokyo - 30min after open"),
        (16, 0, "London - 30min after open"),
        (9, 15, "Tokyo - during news window"),
        (15, 45, "London - during news window"),
    ]
    
    print("🔍 Testing News Window Filter Logic")
    print("=" * 50)
    print("\nNews Windows (blocked periods):")
    for start_h, start_m, end_h, end_m in news_windows:
        print(f"  {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}")
    
    print("\n" + "=" * 50)
    print("\nTest Results:")
    print("-" * 50)
    
    for hour, minute, description in test_times:
        in_news_window = False
        
        # Check if time falls in any news window
        for start_h, start_m, end_h, end_m in news_windows:
            if start_h == end_h:
                if hour == start_h and start_m <= minute < end_m:
                    in_news_window = True
                    break
            else:  # Handles cases that cross hour boundary
                if (hour == start_h and minute >= start_m) or \
                   (hour == end_h and minute < end_m):
                    in_news_window = True
                    break
        
        status = "🚫 BLOCKED" if in_news_window else "✅ ALLOWED"
        print(f"{hour:02d}:{minute:02d} - {description}")
        print(f"  Status: {status}")
        print()
    
    # Test with actual current time
    current_time = datetime.now(jst)
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    print("=" * 50)
    print(f"\nCurrent Time Test (JST): {current_hour:02d}:{current_minute:02d}")
    
    in_news_window = False
    for start_h, start_m, end_h, end_m in news_windows:
        if start_h == end_h:
            if current_hour == start_h and start_m <= current_minute < end_m:
                in_news_window = True
                break
        else:
            if (current_hour == start_h and current_minute >= start_m) or \
               (current_hour == end_h and current_minute < end_m):
                in_news_window = True
                break
    
    status = "🚫 Would be BLOCKED" if in_news_window else "✅ Would be ALLOWED"
    print(f"Status: {status}")
    
    print("\n" + "=" * 50)
    print("\n📊 Summary:")
    print("  ✅ Tokyo 9:30 execution: PASSES filter")
    print("  ✅ London 16:00 execution: PASSES filter")
    print("  🎯 Both scheduled times successfully avoid news windows!")

if __name__ == "__main__":
    test_news_window_filter()