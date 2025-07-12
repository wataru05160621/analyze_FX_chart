#!/usr/bin/env python3
"""
デバッグツール
"""
import asyncio
import sys
from pathlib import Path
from src.logger import setup_logger
from src.main import analyze_fx_charts, _validate_configuration
from src.error_handler import error_recorder
import logging

def print_banner():
    """バナーを表示"""
    print("=" * 60)
    print("🔧 FX Chart Analyzer - Debug Tool")
    print("=" * 60)

def test_configuration():
    """設定をテスト"""
    print("\n📋 設定の検証...")
    try:
        _validate_configuration()
        print("✅ 設定は正常です")
        return True
    except Exception as e:
        print(f"❌ 設定エラー: {e}")
        return False

def test_imports():
    """インポートをテスト"""
    print("\n📦 モジュールのインポートテスト...")
    try:
        from src.tradingview_scraper import TradingViewScraper
        from src.chatgpt_web_analyzer import ChatGPTWebAnalyzer
        from src.chatgpt_analyzer import ChartAnalyzer
        from src.notion_writer import NotionWriter
        from src.image_uploader import get_uploader
        print("✅ すべてのモジュールが正常にインポートされました")
        return True
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        return False

def test_dependencies():
    """依存関係をテスト"""
    print("\n🔗 依存関係のテスト...")
    missing_deps = []
    
    # 必須パッケージ
    try:
        import playwright
        print("✅ playwright: OK")
    except ImportError:
        missing_deps.append("playwright")
        print("❌ playwright: 不足")
    
    try:
        import openai
        print("✅ openai: OK")
    except ImportError:
        missing_deps.append("openai")
        print("❌ openai: 不足")
    
    try:
        import notion_client
        print("✅ notion-client: OK")
    except ImportError:
        missing_deps.append("notion-client")
        print("❌ notion-client: 不足")
    
    try:
        import PyPDF2
        print("✅ PyPDF2: OK")
    except ImportError:
        missing_deps.append("PyPDF2")
        print("❌ PyPDF2: 不足")
    
    # オプションパッケージ
    try:
        import cloudinary
        print("✅ cloudinary: OK (オプション)")
    except ImportError:
        print("⚠️ cloudinary: 不足 (オプション)")
    
    try:
        import boto3
        print("✅ boto3: OK")
    except ImportError:
        missing_deps.append("boto3")
        print("❌ boto3: 不足")
    
    if missing_deps:
        print(f"\n❌ 不足している依存関係: {', '.join(missing_deps)}")
        print("以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    else:
        print("✅ すべての必須依存関係が満たされています")
        return True

async def test_scraper_basic():
    """スクレイパーの基本テスト"""
    print("\n🌐 Trading Viewスクレイパーの基本テスト...")
    try:
        from src.tradingview_scraper import TradingViewScraper
        scraper = TradingViewScraper()
        await scraper.setup()
        print("✅ スクレイパーのセットアップ成功")
        await scraper.close()
        return True
    except Exception as e:
        print(f"❌ スクレイパーテストエラー: {e}")
        return False

async def test_aws_s3():
    """実際AWS S3への接続テスト"""
    print("\n📏 AWS S3接続テスト...")
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # S3クライアントを作成
        s3_client = boto3.client('s3')
        
        # バケット一覧を取得（権限チェック）
        response = s3_client.list_buckets()
        print(f"✅ AWS S3接続成功: {len(response['Buckets'])}個のバケットがあります")
        
        # 設定されたバケットのチェック
        from src.config import AWS_S3_BUCKET
        if AWS_S3_BUCKET and AWS_S3_BUCKET != "fx-analyzer-screenshots-dev":
            try:
                s3_client.head_bucket(Bucket=AWS_S3_BUCKET)
                print(f"✅ 設定されたバケット '{AWS_S3_BUCKET}' にアクセス可能")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print(f"⚠️ バケット '{AWS_S3_BUCKET}' が存在しません")
                else:
                    print(f"⚠️ バケット '{AWS_S3_BUCKET}' へのアクセスエラー: {e}")
        
        return True
        
    except NoCredentialsError:
        print("❌ AWS認証情報が設定されていません")
        print("   AWS CLIで 'aws configure' を実行するか、")
        print("   環境変数でAWS_ACCESS_KEY_IDとAWS_SECRET_ACCESS_KEYを設定してください")
        return False
    except ImportError:
        print("⚠️ boto3パッケージがインストールされていません")
        return False
    except Exception as e:
        print(f"❌ AWS S3テストエラー: {e}")
        return False

async def dry_run():
    """ドライラン（実際のAPIを呼ばない）"""
    print("\n🏃 ドライラン実行...")
    try:
        # モックを使用した疑似実行
        from unittest.mock import patch, AsyncMock, Mock
        
        with patch('src.main.TradingViewScraper') as mock_scraper_class, \
             patch('src.main.ChartAnalyzer') as mock_analyzer_class, \
             patch('src.main.NotionWriter') as mock_notion_class, \
             patch('src.main.USE_WEB_CHATGPT', False):
            
            # モックの設定
            mock_scraper = AsyncMock()
            mock_scraper.capture_charts.return_value = {"5min": Path("/tmp/test.png")}
            mock_scraper_class.return_value = mock_scraper
            
            mock_analyzer = Mock()
            mock_analyzer.analyze_charts.return_value = "テスト分析結果"
            mock_analyzer_class.return_value = mock_analyzer
            
            mock_notion = Mock()
            mock_notion.create_analysis_page.return_value = "test_page_id"
            mock_notion_class.return_value = mock_notion
            
            result = await analyze_fx_charts()
            
            if result["status"] == "success":
                print("✅ ドライラン成功")
                return True
            else:
                print(f"❌ ドライラン失敗: {result.get('error')}")
                return False
                
    except Exception as e:
        print(f"❌ ドライランエラー: {e}")
        return False

def show_error_summary():
    """エラーサマリーを表示"""
    summary = error_recorder.get_summary()
    if summary["total_errors"] > 0:
        print(f"\n📊 エラーサマリー:")
        print(f"総エラー数: {summary['total_errors']}")
        for error_type, count in summary.get("error_types", {}).items():
            print(f"  - {error_type}: {count}件")
    else:
        print("\n✅ エラーは記録されていません")

async def main():
    """メイン関数"""
    print_banner()
    
    # デバッグログを有効化
    setup_logger("debug", level=logging.DEBUG)
    
    # 各テストを実行
    tests = [
        ("設定テスト", test_configuration),
        ("インポートテスト", test_imports),
        ("依存関係テスト", test_dependencies),
        ("AWS S3テスト", test_aws_s3),
        ("スクレイパーテスト", test_scraper_basic),
        ("ドライラン", dry_run)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}で予期しないエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📋 テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n合格: {passed}/{len(results)}")
    
    # エラーサマリーを表示
    show_error_summary()
    
    # 推奨アクション
    print("\n💡 推奨アクション:")
    if passed == len(results):
        print("✅ すべてのテストが通りました！本番実行を試してください。")
        print("   python -m src.main")
    else:
        print("❌ いくつかのテストが失敗しました。以下を確認してください:")
        print("   1. 依存関係のインストール: pip install -r requirements.txt")
        print("   2. 環境変数の設定: .envファイルの確認")
        print("   3. Playwrightのセットアップ: playwright install")

if __name__ == "__main__":
    asyncio.run(main())