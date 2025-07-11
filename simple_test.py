#!/usr/bin/env python3
"""
簡易テスト - チャート生成と分析の品質確認
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_chart_generation():
    """チャート生成のテスト"""
    print("=== チャート生成テスト ===")
    
    try:
        from src.chart_generator import ChartGenerator
        
        generator = ChartGenerator('USDJPY=X')
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        # チャート生成
        screenshots = generator.generate_multiple_charts(
            timeframes=['5min', '1hour'],
            output_dir=output_dir,
            candle_count=288
        )
        
        print("✅ チャート生成成功")
        for tf, path in screenshots.items():
            if path.exists():
                size_kb = path.stat().st_size / 1024
                print(f"  {tf}: {path.name} ({size_kb:.1f} KB)")
            else:
                print(f"  {tf}: ❌ ファイルが存在しません")
                
        return screenshots
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_claude_analysis(screenshots):
    """Claude分析のテスト"""
    print("\n=== Claude分析テスト ===")
    
    if not screenshots:
        print("❌ チャート画像がありません")
        return None
        
    try:
        from src.claude_analyzer import ClaudeAnalyzer
        
        analyzer = ClaudeAnalyzer()
        
        # PDFコンテンツ確認
        if analyzer.book_content:
            print(f"✅ PDF読み込み済み: {len(analyzer.book_content)}文字")
        else:
            print("⚠️ PDFが読み込まれていません")
        
        # 分析実行
        print("分析実行中...")
        analysis = analyzer.analyze_charts(screenshots)
        
        print(f"✅ 分析完了: {len(analysis)}文字")
        
        # 品質チェック
        keywords = ["ビルドアップ", "EMA", "サポート", "レジスタンス", "エントリー"]
        found = sum(1 for kw in keywords if kw in analysis)
        print(f"品質キーワード: {found}/{len(keywords)}")
        
        # 分析の一部を表示
        print("\n分析内容（最初の500文字）:")
        print("-" * 50)
        print(analysis[:500])
        print("-" * 50)
        
        return analysis
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_blog_format(analysis):
    """ブログフォーマットのテスト"""
    print("\n=== ブログフォーマットテスト ===")
    
    if not analysis:
        print("❌ 分析結果がありません")
        return
        
    # ブログ用フォーマット（二重分析なし）
    blog_content = f"""**本記事は投資判断を提供するものではありません。**FXチャートの分析手法を学習する目的で、現在のチャート状況を解説しています。実際の売買は自己責任で行ってください。

{analysis}

---
※このブログ記事は教育目的で作成されています。投資は自己責任でお願いします。"""
    
    print(f"✅ ブログフォーマット完了: {len(blog_content)}文字")
    print("✅ 二重分析を回避（既存の分析を再利用）")
    
    # テスト結果を保存
    output_file = Path("test_output/test_blog.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# テストブログ記事\n\n")
        f.write(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(blog_content)
    
    print(f"✅ テスト結果を保存: {output_file}")

def main():
    """メイン処理"""
    print(f"テスト開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. チャート生成
    screenshots = test_chart_generation()
    
    # 2. Claude分析
    analysis = test_claude_analysis(screenshots)
    
    # 3. ブログフォーマット
    test_blog_format(analysis)
    
    print(f"\n✅ テスト完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()