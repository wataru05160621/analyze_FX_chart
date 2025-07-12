# 複数通貨ペア分析の実行

以下のコマンドをターミナルで実行してください：

```bash
cd /Users/shinzato/programing/claude_code/analyze_FX_chart
./venv/bin/python run_multi_currency.py
```

## 実行内容

このコマンドは以下を実行します：

1. **USD/JPY（ドル円）**
   - 5分足・1時間足チャート生成
   - Claude AIによる分析
   - Notionに保存（Currency: USD/JPY）

2. **XAU/USD（ゴールド）**
   - 5分足・1時間足チャート生成
   - Claude AIによる分析
   - Notionに保存（Currency: XAU/USD）

3. **BTC/USD（ビットコイン）**
   - 5分足・1時間足チャート生成
   - Claude AIによる分析
   - Notionに保存（Currency: BTC/USD）

## 確認事項

実行後、以下を確認してください：

1. **Notionデータベース**
   - 3つの新しいエントリが作成されている
   - Currencyフィールドでフィルタリングが可能

2. **ローカルファイル**
   - `analysis_summary.md` - 実行サマリー
   - `screenshots/USD_JPY/` - ドル円チャート
   - `screenshots/XAU_USD/` - ゴールドチャート
   - `screenshots/BTC_USD/` - ビットコインチャート

## デバッグが必要な場合

```bash
./venv/bin/python run_multi_currency.py --debug
```