#!/usr/bin/env python3
"""
通貨ペアごとのチャートスケールテスト
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.chart_generator import ChartGenerator

def test_chart_scales():
    """各通貨ペアのチャートスケールをテスト"""
    print("=== チャートスケールテスト ===\n")
    
    test_pairs = [
        ('USD/JPY', 'USDJPY=X', 'ドル円'),
        ('XAU/USD', 'GC=F', 'ゴールド'),
        ('BTC/USD', 'BTC-USD', 'ビットコイン'),
    ]
    
    output_dir = Path("test_charts")
    output_dir.mkdir(exist_ok=True)
    
    for pair_name, symbol, name_jp in test_pairs:
        print(f"\n{pair_name} ({name_jp}) のチャート生成中...")
        
        try:
            generator = ChartGenerator(symbol)
            
            # 5分足チャート生成
            chart_path = generator.generate_chart(
                timeframe="5min",
                output_dir=output_dir,
                candle_count=100
            )
            print(f"  ✅ 5分足チャート: {chart_path}")
            
            # チャートの価格スケール情報
            if 'BTC' in symbol:
                print("  価格スケール: $50-$1,000刻み（価格範囲に応じて自動調整）")
            elif 'GC=F' in symbol:
                print("  価格スケール: $5-$20刻み（価格範囲に応じて自動調整）")
            else:
                print("  価格スケール: 0.1円刻み")
                
        except Exception as e:
            print(f"  ❌ エラー: {e}")
    
    print(f"\n\nテストチャートは {output_dir} に保存されました。")
    print("各チャートのY軸目盛りを確認してください。")

if __name__ == "__main__":
    test_chart_scales()