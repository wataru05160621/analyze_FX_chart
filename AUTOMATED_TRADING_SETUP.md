# Phase1 自動トレード記録システム

## 概要
トレードの記録を完全自動化する3つの方法を実装しました。

## 1. MT4レポート自動監視

### 仕組み
- MT4が生成するHTMLレポートを自動監視
- 新規トレードを検出して自動記録
- AI分析でセットアップタイプを推定

### セットアップ
```bash
# MT4のFilesフォルダパスを設定
# Windows: C:/Users/[Username]/AppData/Roaming/MetaQuotes/Terminal/[ID]/MQL4/Files
# Mac: /Users/[Username]/Library/Application Support/MetaTrader 4/[ID]/MQL4/Files

# 監視開始
python src/mt4_auto_recorder.py
```

### MT4側の設定
```mql4
// Expert Advisorに追加
void OnTradeClose() {
    // レポート生成
    string filename = "report_" + TimeToString(TimeCurrent()) + ".htm";
    ReportSave(filename);
}
```

## 2. デモトレード自動実行

### 仕組み
- 5分ごとに市場を自動分析
- Volmanセットアップを検出
- 自動エントリー・決済・記録

### 実行方法
```bash
# デモトレード開始
python src/phase1_demo_trader.py

# バックグラウンド実行
nohup python src/phase1_demo_trader.py > logs/demo_trader.log 2>&1 &
```

### 特徴
- **完全自動**: 人の介入不要
- **24時間稼働**: 全セッション対応
- **品質フィルター**: 3つ星以上のみエントリー
- **リスク管理**: 20/10固定

## 3. TradingView Webhook連携

### 仕組み
```
TradingView Alert → Webhook → Python → Database
```

### 設定
1. TradingViewアラート作成
```javascript
// Pine Script
alertcondition(entry_signal, 
    title="Volman Entry",
    message='{"action":"entry","setup":"A","price":{{close}},"quality":4}')
```

2. Webhook受信サーバー
```python
# すでに実装済み: src/phase1_webhook_server.py
python src/phase1_webhook_server.py
```

## 自動収集されるデータ

### トレードごと
- エントリー/エグジット時刻・価格
- セットアップタイプ（A-F）
- ビルドアップパターン
- EMA配列状態
- 最大含み益/損（MFE/MAE）
- チャート画像（自動生成）
- AI分析結果

### 5分ごと
- 価格とEMA
- ATR、スプレッド
- セッション情報

### 日次
- 勝率、総pips
- プロフィットファクター
- セットアップ別成績

## データ確認方法

### リアルタイムモニタリング
```python
from src.phase1_data_collector import Phase1DataCollector

collector = Phase1DataCollector()

# 本日の成績
summary = collector.get_performance_summary(
    start_date=datetime.now().strftime('%Y-%m-%d'),
    end_date=datetime.now().strftime('%Y-%m-%d')
)
print(summary)
```

### Notionダッシュボード
- 自動的に更新
- グラフとチャート付き
- モバイルからも確認可能

### Slack通知
```
🟢 デモトレード結果
ID: DEMO_20240315_143022
セットアップ: A
結果: 20.0 pips (TP)
品質: ⭐⭐⭐⭐
保有時間: 35分
```

## トラブルシューティング

### トレードが記録されない
1. プロセス確認: `ps aux | grep phase1`
2. ログ確認: `tail -f logs/demo_trader.log`
3. データベース確認: `sqlite3 phase1_data/phase1_trades.db`

### 分析精度が低い
- チャート画像の品質確認
- Claude API制限確認
- プロンプトの調整

## 推奨運用

### Phase 1（3ヶ月）
1. **デモトレード自動実行**を24時間稼働
2. 週次でパフォーマンスレビュー
3. 月次で戦略調整

### データ活用
- セットアップ別勝率分析
- 時間帯別パフォーマンス
- ビルドアップ品質と結果の相関

これにより、実際にトレードしなくても自動的にデータが蓄積され、Phase 3のAI学習に必要な高品質データセットが構築されます。