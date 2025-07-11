import os
import sys
sys.path.insert(0, '.')

# 環境変数の状態を確認
print("=== 環境変数チェック ===")

# .env.phase1から読み込み
if os.path.exists('.env.phase1'):
    with open('.env.phase1', 'r') as f:
        for line in f:
            if 'SLACK_WEBHOOK_URL' in line and '=' in line:
                key, value = line.strip().split('=', 1)
                if value and not value.startswith('#'):
                    os.environ[key] = value
                    print(f"SLACK_WEBHOOK_URL: 設定済み ({value[:30]}...)")
            elif 'ENABLE_PHASE1' in line and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
                print(f"ENABLE_PHASE1: {value}")

# Slack通知テスト
if os.environ.get('ENABLE_PHASE1') == 'true' and os.environ.get('SLACK_WEBHOOK_URL'):
    print("\nSlack通知を送信中...")
    import requests
    
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    response = requests.post(
        webhook_url,
        json={"text": f"FX分析システム: 出力テスト実行中 {os.popen('date').read().strip()}"}
    )
    
    if response.status_code == 200:
        print("✅ Slack通知送信成功！")
    else:
        print(f"❌ 送信失敗: {response.status_code}")
        print(response.text)
else:
    print("\n❌ Slack通知は無効です")