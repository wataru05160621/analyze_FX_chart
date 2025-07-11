# FX分析システム品質改善計画

## 実施する修正

### 1. ブログ投稿フローの最適化（最優先）

現在の問題：
- `MultiCurrencyAnalyzer`で一度分析を実行
- その後`BlogAnalyzer`で**再度**分析を実行（二重処理）

解決策：
```python
# main_multi_currency.pyの修正
# 103-104行目を以下に変更:
# ブログ用の分析を生成 ← これを削除
# blog_analyzer = BlogAnalyzer()
# blog_analysis = blog_analyzer.analyze_for_blog(results['USD/JPY']['screenshots'])

# 代わりに既存の分析結果を使用:
blog_analysis = results['USD/JPY']['analysis']

# またはフォーマット関数を作成:
def format_analysis_for_blog(analysis_text):
    # 分析テキストをブログ用にフォーマット
    return formatted_text
```

### 2. チャート画像パスの確実な受け渡し

現在の問題：
- チャート画像がブログに含まれない
- スクリーンショットパスが正しく渡されていない

解決策：
```python
# blog_publisher.pyの修正
def publish_analysis(self, analysis_text, chart_images):
    # chart_imagesが辞書形式であることを確認
    # {'5min': Path('screenshots/USD_JPY/5min.png'), ...}
    
    # 各画像をWordPressにアップロード
    uploaded_images = {}
    for timeframe, image_path in chart_images.items():
        if image_path.exists():
            media_data = self.upload_media_to_wordpress(image_path)
            if media_data:
                uploaded_images[timeframe] = media_data['source_url']
```

### 3. 分析品質の向上

現在の使用状況：
- ClaudeAnalyzerは正しくフル機能版を使用
- プロンプトは詳細（300行以上）
- 書籍内容も読み込まれている

追加改善案：
1. **モデルの確認**: claude-3-5-sonnet-20241022が使用されているか確認
2. **トークン数の増加**: max_tokens=4000は十分か検証
3. **画像品質の確認**: チャート画像が正しくエンコードされているか

### 4. 実装手順

```bash
# 1. バックアップ作成
cp src/main_multi_currency.py src/main_multi_currency.py.backup
cp src/blog_publisher.py src/blog_publisher.py.backup

# 2. 修正実施
# - main_multi_currency.pyの二重分析を解消
# - blog_publisher.pyの画像処理を改善

# 3. テスト実行
python test_blog_quality.py
```

## テストスクリプト

以下のテストスクリプトで品質を確認：

```python
# test_blog_quality.py
import asyncio
from src.multi_currency_analyzer import MultiCurrencyAnalyzer
from src.blog_publisher import BlogPublisher

async def test_blog_quality():
    # 1. 通常の分析を実行
    analyzer = MultiCurrencyAnalyzer()
    results = await analyzer.analyze_currency_pair('USD/JPY', {...})
    
    # 2. 分析結果の品質確認
    print(f"分析文字数: {len(results['analysis'])}")
    print(f"チャート画像数: {len(results['screenshots'])}")
    
    # 3. ブログ投稿準備（実際には投稿しない）
    # ...

asyncio.run(test_blog_quality())
```

## 期待される改善効果

1. **処理時間**: 二重分析解消により50%短縮
2. **API費用**: Claude API呼び出しが半減
3. **一貫性**: 分析とブログ内容が完全一致
4. **画像表示**: チャート画像が確実に表示される
5. **分析品質**: フル機能のClaudeAnalyzerで詳細分析