#!/usr/bin/env python3
"""
8時モードでブログ投稿を実行
"""
import os
import sys
import subprocess

print("=== FX分析システム ブログ投稿実行 ===")
print("8時モードで実行（ブログ投稿有効）")
print()

# 環境変数を設定
env = os.environ.copy()
env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
env['FORCE_HOUR'] = '8'  # 8時モードを強制

# .envファイルから環境変数を読み込み
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if value and value not in ['your_value_here', 'your_api_key_here']:
                    env[key] = value

# .env.phase1から読み込み
if os.path.exists('.env.phase1'):
    with open('.env.phase1', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env[key] = value

print("設定確認:")
print(f"ENABLE_BLOG_POSTING: {env.get('ENABLE_BLOG_POSTING')}")
print(f"WORDPRESS_URL: {env.get('WORDPRESS_URL')}")
print(f"TWITTER_API_KEY: {'設定済み' if env.get('TWITTER_API_KEY') else '未設定'}")
print()

# メインプログラムを実行
print("分析とブログ投稿を開始...")
try:
    result = subprocess.run(
        [sys.executable, '-m', 'src.main_multi_currency'],
        env=env,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print("\n実行結果:")
    print(result.stdout)
    
    if result.stderr:
        print("\nエラー:")
        print(result.stderr)
    
    # ログファイルの最新エントリを確認
    print("\n最新のログ:")
    if os.path.exists('logs/fx_analysis.log'):
        with open('logs/fx_analysis.log', 'r') as f:
            lines = f.readlines()
            recent = lines[-20:]
            for line in recent:
                if any(word in line for word in ['WordPress', 'Twitter', 'ブログ', '投稿']):
                    print(f"  {line.strip()}")
    
except Exception as e:
    print(f"実行エラー: {e}")
    import traceback
    traceback.print_exc()

print("\n投稿先を確認してください:")
print("- WordPress: https://by-price-action.com")
print("- Twitter: 設定したアカウント")
print("- Notion: データベースページ")
print("- Slack: 設定したチャンネル")