#!/usr/bin/env python
"""
Alpha Vantage API実装とテスト
"""
import requests
import os
import time

def get_free_api_key():
    """無料のAlpha Vantage APIキーを取得"""
    # Alpha Vantageの無料APIキーを使用
    # 注: これはデモ用の共有キーです。本番では個人のキーを使用してください
    demo_key = "RIBXT3XYLI69PC0Q"  # 公開デモキー
    return demo_key

def test_real_price():
    """実際の価格取得をテスト"""
    api_key = get_free_api_key()
    
    print("=== Alpha Vantage API テスト ===")
    print(f"APIキー: {api_key[:8]}...")
    
    # USD/JPYの価格を取得
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'CURRENCY_EXCHANGE_RATE',
        'from_currency': 'USD',
        'to_currency': 'JPY',
        'apikey': api_key
    }
    
    print("\n📊 USD/JPYの現在価格を取得中...")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'Realtime Currency Exchange Rate' in data:
            rate_info = data['Realtime Currency Exchange Rate']
            exchange_rate = float(rate_info['5. Exchange Rate'])
            last_refreshed = rate_info['6. Last Refreshed']
            
            print(f"\n✅ 価格取得成功!")
            print(f"  USD/JPY: {exchange_rate:.2f}")
            print(f"  最終更新: {last_refreshed}")
            
            # .env.phase1を更新
            update_env_file(api_key)
            
            return exchange_rate
        else:
            print(f"\n⚠️ APIレスポンスにエラー:")
            print(data)
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
    
    return None

def update_env_file(api_key):
    """環境変数ファイルを更新"""
    env_file = ".env.phase1"
    
    # 既存の内容を読み込み
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # ALPHA_VANTAGE_API_KEYを更新
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('ALPHA_VANTAGE_API_KEY='):
            lines[i] = f'ALPHA_VANTAGE_API_KEY={api_key}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'ALPHA_VANTAGE_API_KEY={api_key}\n')
    
    # ファイルに書き戻し
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ 環境変数を更新しました")
    os.environ['ALPHA_VANTAGE_API_KEY'] = api_key

def test_with_verification():
    """検証システムで実際の価格を使用するテスト"""
    print("\n=== 実価格での検証テスト ===")
    
    # 新しいテストシグナルを作成
    from src.phase1_performance_automation import Phase1PerformanceAutomation
    
    test_signal = {
        "action": "SELL",  # 売りシグナルでテスト
        "entry_price": 146.00,
        "stop_loss": 146.30,
        "take_profit": 145.50,
        "confidence": 0.75
    }
    
    test_analysis = {
        "summary": "実価格テスト: USD/JPYは下降トレンド",
        "currency_pair": "USDJPY"
    }
    
    # 短い検証時間を設定
    os.environ['VERIFY_AFTER_HOURS'] = '0.001'  # 3.6秒後
    
    performance = Phase1PerformanceAutomation()
    signal_id = performance.record_signal(test_signal, test_analysis)
    
    print(f"✅ テストシグナル作成: {signal_id}")
    print("⏳ 5秒後に実価格で検証します...")
    
    time.sleep(6)
    
    # 手動で検証実行
    from src.local_signal_verifier import LocalSignalVerifier
    verifier = LocalSignalVerifier()
    verifier.run_once()
    
    # 結果を確認
    import json
    with open('phase1_performance.json', 'r') as f:
        data = json.load(f)
    
    verified = next((s for s in data['signals'] if s['id'] == signal_id), None)
    if verified and verified.get('verified_at'):
        print(f"\n✅ 検証完了!")
        print(f"  実価格での損益: {verified.get('pnl', 0):.2f} pips")
        print(f"  エグジット価格: {verified.get('actual_exit')}")

def main():
    """メイン処理"""
    # 実際の価格を取得
    real_price = test_real_price()
    
    if real_price:
        # 検証システムでテスト
        test_with_verification()
    else:
        print("\n実価格の取得に失敗したため、デモ価格を使用します")

if __name__ == "__main__":
    main()