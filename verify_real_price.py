#!/usr/bin/env python
"""
実価格の動作確認
"""
import os
import requests

# 環境変数を手動で設定
os.environ['ALPHA_VANTAGE_API_KEY'] = 'RIBXT3XYLI69PC0Q'

api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
print(f"APIキー: {api_key[:8]}...")

# 直接価格を取得
url = "https://www.alphavantage.co/query"
params = {
    'function': 'CURRENCY_EXCHANGE_RATE',
    'from_currency': 'USD',
    'to_currency': 'JPY',
    'apikey': api_key
}

print("\nUSD/JPYの価格を取得中...")
response = requests.get(url, params=params, timeout=10)
data = response.json()

if 'Realtime Currency Exchange Rate' in data:
    rate_info = data['Realtime Currency Exchange Rate']
    rate = float(rate_info['5. Exchange Rate'])
    print(f"✅ 現在のUSD/JPY: {rate:.2f}")
else:
    print("❌ 価格取得失敗")
    print(data)