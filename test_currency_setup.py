#!/usr/bin/env python3
"""
通貨ペア設定の確認スクリプト
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.multi_currency_analyzer import CURRENCY_PAIRS
from src.notion_writer import NotionWriter

def test_currency_setup():
    """通貨ペア設定の確認"""
    print("=== 通貨ペア設定確認 ===\n")
    
    # 1. 通貨ペア設定の確認
    print("1. 設定されている通貨ペア:")
    for pair_name, config in CURRENCY_PAIRS.items():
        print(f"   - {pair_name}: {config['name']} ({config['symbol']})")
        print(f"     説明: {config['description']}")
    
    # 2. NotionWriter の currency パラメータ確認
    print("\n2. NotionWriter の create_analysis_page メソッド:")
    import inspect
    signature = inspect.signature(NotionWriter.create_analysis_page)
    print(f"   シグネチャ: {signature}")
    print("   ✅ currency パラメータが追加されています" if 'currency' in signature.parameters else "   ❌ currency パラメータがありません")
    
    # 3. 実行手順の説明
    print("\n3. 実行方法:")
    print("   通常の実行:")
    print("   $ ./venv/bin/python run_multi_currency.py")
    print("\n   デバッグモード:")
    print("   $ ./venv/bin/python run_multi_currency.py --debug")
    
    print("\n4. 期待される動作:")
    print("   - USD/JPY, XAU/USD, BTC/USD の3つの通貨ペアを並行して分析")
    print("   - 各通貨ペアの分析結果をNotionに保存")
    print("   - Currency フィールドに適切な通貨ペア名を設定")
    print("   - 分析サマリーレポートを analysis_summary.md に保存")

if __name__ == "__main__":
    test_currency_setup()