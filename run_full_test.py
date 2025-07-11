#!/usr/bin/env python3
"""
フルシステムテストを実行
"""
import os
import sys
import asyncio
from datetime import datetime

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def run_full_test():
    """フルシステムテストを実行"""
    
    print("=== FX分析システム 統合テスト ===")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 8時のブログ投稿モードをシミュレート
    os.environ['FORCE_HOUR'] = '8'
    os.environ['TEST_MODE'] = 'true'  # テストモード
    
    print("1. 環境設定:")
    print(f"   FORCE_HOUR: 8 (ブログ投稿モード)")
    print(f"   TEST_MODE: true")
    
    # Phase 1の環境変数を読み込み
    if os.path.exists('.env.phase1'):
        with open('.env.phase1', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("   ✅ .env.phase1を読み込みました")
    
    # メインの環境変数を読み込み
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
        print("   ✅ .envを読み込みました")
    
    print("\n2. システムテストを開始:")
    
    try:
        # main_multi_currencyをインポートして実行
        from src.main_multi_currency import analyze_fx_multi_currency
        
        print("   分析を実行中...")
        result = await analyze_fx_multi_currency()
        
        if result.get("status") == "success":
            print("\n   ✅ 分析完了!")
            
            # 結果の確認
            if 'results' in result:
                for currency, data in result['results'].items():
                    if data.get('status') == 'success':
                        print(f"\n   {currency}:")
                        print(f"      分析文字数: {len(data.get('analysis', ''))}")
                        print(f"      チャート数: {len(data.get('screenshots', {}))}")
                    else:
                        print(f"\n   {currency}: エラー")
            
        else:
            print(f"\n   ❌ エラー: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n   ❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n3. ログファイルの確認:")
    
    # 最新のログを確認
    log_files = [
        'logs/fx_analysis.log',
        'logs/src.main_multi_currency_errors.log',
        'logs/phase1_202507.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n   {log_file}:")
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # 最後の10行を表示
                recent_lines = lines[-10:] if len(lines) > 10 else lines
                for line in recent_lines:
                    if 'ERROR' in line or 'WARNING' in line:
                        print(f"      {line.strip()}")
                    elif 'WordPress' in line or 'ブログ' in line:
                        print(f"      {line.strip()}")
    
    print("\n4. 出力ファイルの確認:")
    
    # 生成されたファイルを確認
    output_files = [
        'analysis_summary.json',
        'phase1_performance.json',
        'screenshots/USD_JPY/5min.png',
        'screenshots/USD_JPY/1hour.png'
    ]
    
    for file_path in output_files:
        if os.path.exists(file_path):
            if file_path.endswith('.png'):
                size = os.path.getsize(file_path) / 1024
                print(f"   ✅ {file_path} ({size:.1f} KB)")
            else:
                print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (見つかりません)")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    # 非同期関数を実行
    asyncio.run(run_full_test())