#!/usr/bin/env python3
"""
環境変数の問題を修正するスクリプト
"""
import os

# .envファイルを読み込んで修正
env_file = '.env'
env_backup = '.env.backup'

# バックアップ作成
with open(env_file, 'r') as f:
    content = f.read()
    
with open(env_backup, 'w') as f:
    f.write(content)
    
print(f"✅ バックアップ作成: {env_backup}")

# 修正が必要な行
fixes = {
    'WORDPRESS_CATEGORY_USDJPY=4  # ドル円カテゴリID': 'WORDPRESS_CATEGORY_USDJPY=4',
    'WORDPRESS_CATEGORY_ANALYSIS=3  # 分析カテゴリID': 'WORDPRESS_CATEGORY_ANALYSIS=3',
    'WORDPRESS_TAG_DAILY_USDJPY=2  # 日次ドル円分析タグID': 'WORDPRESS_TAG_DAILY_USDJPY=2'
}

# .envファイルを修正
lines = content.split('\n')
new_lines = []

for line in lines:
    fixed = False
    for old, new in fixes.items():
        if line.strip() == old:
            new_lines.append(new)
            print(f"修正: {old} → {new}")
            fixed = True
            break
    if not fixed:
        new_lines.append(line)

# 修正内容を保存
with open(env_file, 'w') as f:
    f.write('\n'.join(new_lines))
    
print("\n✅ .envファイルの修正完了")

# ANTHROPIC_API_KEY追加（CLAUDE_API_KEYと同じ値）
add_anthropic = False
with open(env_file, 'r') as f:
    content = f.read()
    if 'ANTHROPIC_API_KEY' not in content and 'CLAUDE_API_KEY' in content:
        add_anthropic = True

if add_anthropic:
    # CLAUDE_API_KEYの値を取得
    for line in content.split('\n'):
        if line.startswith('CLAUDE_API_KEY='):
            claude_key = line.split('=', 1)[1]
            # ANTHROPIC_API_KEYを追加
            with open(env_file, 'a') as f:
                f.write(f"\n# Anthropic API設定（Claude API用）\nANTHROPIC_API_KEY={claude_key}\n")
            print(f"✅ ANTHROPIC_API_KEY追加")
            break

print("\n修正内容:")
print("1. WordPressカテゴリ/タグIDのコメントを削除")
print("2. ANTHROPIC_API_KEYを追加（CLAUDE_API_KEYと同じ値）")
print("\n次のコマンドを実行してください:")
print("python3 execute_with_enhanced_haiku.py")