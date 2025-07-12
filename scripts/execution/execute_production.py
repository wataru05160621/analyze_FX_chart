#!/usr/bin/env python3
"""
本番システムで実分析を実行
"""
import os
import subprocess
import sys

print("=== FX分析システム 本番実行 ===")
print("8時モードで実行（ブログ投稿有効）\n")

# 環境変数を設定
env = os.environ.copy()
env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
env['FORCE_HOUR'] = '8'  # 8時モードを強制
env['ENABLE_BLOG_POSTING'] = 'true'

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

print("実行中...")

# main_multi_currencyを実行
try:
    # USD/JPYのみの分析にするため、環境変数で制御
    env['SINGLE_CURRENCY_MODE'] = 'true'
    
    result = subprocess.run(
        [sys.executable, '-m', 'src.main_multi_currency'],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print("\n実行完了!")
    print("\n確認先:")
    print("- Slack: 設定したチャンネル")
    print("- Notion: データベース")
    print("- WordPress: https://by-price-action.com/wp-admin/")
    print("- ログ: logs/fx_analysis.log")
    
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()