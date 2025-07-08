#!/usr/bin/env python3
"""
複数通貨ペア（USD/JPY, XAU/USD, BTC/USD）の分析を実行
"""
import asyncio
import sys
from pathlib import Path
import logging

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.multi_currency_analyzer import run_multi_currency_analysis
from src.logger import setup_logger

# ログ設定
logger = setup_logger(__name__, level=logging.INFO)

async def main():
    """メイン実行関数"""
    print("=== 複数通貨ペア分析 ===")
    print("対象通貨ペア:")
    print("  1. USD/JPY (ドル円)")
    print("  2. XAU/USD (ゴールド)")
    print("  3. BTC/USD (ビットコイン)")
    print()
    
    try:
        # 複数通貨ペアの分析を実行
        results = await run_multi_currency_analysis()
        
        print("\n=== 分析完了 ===")
        for pair_name, result in results.items():
            if result.get('status') == 'success':
                print(f"✅ {pair_name}: 成功")
            else:
                print(f"❌ {pair_name}: 失敗 - {result.get('error', 'Unknown error')}")
        
        print("\n結果はNotionに保存されました。")
        print("サマリーレポート: analysis_summary.md")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        logger.error(f"実行エラー: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # デバッグモード
    if "--debug" in sys.argv:
        setup_logger(__name__, level=logging.DEBUG)
    
    # 実行
    asyncio.run(main())