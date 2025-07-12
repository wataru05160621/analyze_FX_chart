#!/usr/bin/env python3
"""
全フローのテスト実行スクリプト
AM8:00モード（3通貨分析 + USD/JPYブログ投稿）をテスト
"""
import os
import sys
import asyncio
from datetime import datetime

# 環境変数を設定（AM8:00モードを強制）
os.environ["FORCE_HOUR"] = "8"

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.logger import setup_logger

logger = setup_logger(__name__)

async def test_full_flow():
    """全フローをテスト実行"""
    try:
        logger.info("=" * 60)
        logger.info("全フローテスト開始 (AM8:00モード)")
        logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # メインモジュールをインポート
        from src.main_multi_currency import analyze_fx_multi_currency
        
        # 実行
        result = await analyze_fx_multi_currency()
        
        if result["status"] == "success":
            logger.info("\n✅ テスト成功！")
            logger.info("以下の処理が実行されました：")
            logger.info("1. USD/JPY, BTC/USD, XAU/USD の3通貨分析")
            logger.info("2. 各通貨の分析結果をNotionに保存")
            logger.info("3. USD/JPYのブログ記事をWordPressに投稿")
            logger.info("4. USD/JPYの要約をX（Twitter）に投稿")
        else:
            logger.error(f"\n❌ テスト失敗: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"テスト実行エラー: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    print("\n🚀 FXチャート分析システム - 全フローテスト開始\n")
    print("このテストでは以下を実行します：")
    print("1. 3通貨（USD/JPY, BTC/USD, XAU/USD）のチャート生成")
    print("2. Claude APIによる各通貨の詳細分析")
    print("3. Notionへの分析結果保存")
    print("4. USD/JPYのWordPress/X投稿（設定されている場合）")
    print("\n⚠️  注意: このテストは実際にAPIを使用し、Notionやブログに投稿します")
    
    response = input("\n続行しますか？ (y/n): ")
    if response.lower() != 'y':
        print("テストを中止しました")
        sys.exit(0)
    
    # テスト実行
    asyncio.run(test_full_flow())