#!/usr/bin/env python3
"""
Notion詳細分析のテストスクリプト
環境認識、ビルドアップ、ダマシ分析を含む
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("=== Notion詳細分析テスト ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数読み込み
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            if '#' in line:
                line = line.split('#')[0].strip()
            key, value = line.strip().split('=', 1)
            if value and value not in ['your_value_here', 'your_api_key_here']:
                os.environ[key] = value

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.notion_analyzer import NotionAnalyzer

# 1. チャート生成
print("\n1. チャート生成...")
generator = ChartGenerator('USDJPY=X')
output_dir = Path('screenshots') / f"notion_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
output_dir.mkdir(parents=True, exist_ok=True)

screenshots = generator.generate_multiple_charts(
    timeframes=['5min', '1hour'],
    output_dir=output_dir,
    candle_count=288
)
print(f"✅ チャート生成完了")

# 2. Claude分析
print("\n2. Claude分析...")
analyzer = ClaudeAnalyzer()
try:
    analysis = analyzer.analyze_charts(screenshots)
    print(f"✅ 分析完了: {len(analysis)}文字")
except Exception as e:
    print(f"❌ 分析エラー: {e}")
    sys.exit(1)

# 3. Notion用詳細分析生成
print("\n3. Notion用詳細分析生成...")
notion_analyzer = NotionAnalyzer()
detailed_analysis = notion_analyzer.create_detailed_analysis(analysis)
print(f"✅ 詳細分析生成完了: {len(detailed_analysis)}文字")

# 詳細分析のプレビュー
print("\n=== 詳細分析プレビュー ===")
print(detailed_analysis[:1500])
print("\n... (以下省略) ...\n")

# 追加された要素の確認
print("=== 追加要素チェック ===")
checks = {
    "環境認識": "環境認識" in detailed_analysis,
    "セッション分析": "セッション" in detailed_analysis,
    "ボラティリティ分析": "ボラティリティ" in detailed_analysis,
    "ビルドアップ詳細": "ビルドアップ分析" in detailed_analysis,
    "ダマシ分析": "ティーズブレイク" in detailed_analysis or "ダマシ" in detailed_analysis,
    "リスク評価": "リスク評価" in detailed_analysis,
    "Volman七原則": "七原則" in detailed_analysis,
    "トレードチェックリスト": "チェックリスト" in detailed_analysis,
}

for element, exists in checks.items():
    print(f"   {element}: {'✅' if exists else '❌'}")

# 分析を保存
with open('notion_detailed_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(detailed_analysis)
print(f"\n✅ 詳細分析保存: notion_detailed_analysis.txt")

# 4. Notion投稿
print("\n4. Notion投稿テスト...")
try:
    writer = NotionWriter()
    page_id = writer.create_analysis_page(
        f"[詳細版テスト] USD/JPY分析 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        detailed_analysis,
        screenshots,
        "USD/JPY"
    )
    print(f"✅ Notion投稿成功: {page_id}")
    print(f"   URL: https://notion.so/{page_id.replace('-', '')}")
    
    print("\n投稿内容:")
    print("- エグゼクティブサマリー")
    print("- 環境認識（セッション、ボラティリティ、マクロ構造）")
    print("- プライスアクション詳細（ビルドアップ、S/R、EMA）")
    print("- リスク評価とダマシ分析")
    print("- トレードプラン詳細")
    print("- Volman七原則の適用")
    print("- オリジナルClaude分析")
    print("- トレード記録用メモ")
    
except Exception as e:
    print(f"❌ Notionエラー: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ テスト完了!")
print("\nNotionで確認してください:")
print("1. 詳細な環境認識セクション")
print("2. ビルドアップの詳細分析")
print("3. ダマシ（ティーズブレイク）の警告")
print("4. トレード前チェックリスト")
print("5. 学習ポイントのメモセクション")