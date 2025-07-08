# Phase 1: FX Trading Alert System

## 概要
Phase 1では、FX分析結果から自動的に売買シグナルを生成し、Slackに通知するアラートシステムを実装しました。

## 主な機能
- 分析テキストから売買シグナル（BUY/SELL/NONE）を自動生成
- エントリー価格、損切り、利確レベルの自動抽出
- Slack Webhookによるリアルタイム通知
- シグナルのパフォーマンス記録と統計

## ファイル構成
```
├── src/
│   ├── phase1_alert_system.py      # アラートシステムのコア実装
│   └── phase1_integration.py        # 既存システムとの統合
├── tests/
│   └── test_phase1_alert_system.py  # テストコード（TDD）
├── doc/
│   ├── phase1_setup_guide.md        # セットアップガイド
│   └── phase1_readme.md             # このファイル
├── .env.phase1.example              # 環境変数テンプレート
├── run_phase1_demo_simple.py        # デモ実行スクリプト
├── run_phase1_production.py         # 本番実行スクリプト
├── check_phase1_performance.py      # パフォーマンス確認
└── setup_cron_phase1.sh             # Cron設定スクリプト
```

## クイックスタート

### 1. 環境設定
```bash
# 環境変数ファイルを作成
cp .env.phase1.example .env.phase1

# Slack Webhook URLを設定
# .env.phase1 を編集してSLACK_WEBHOOK_URLを設定
```

### 2. デモ実行
```bash
# シンプルなデモ（Slackに2つのテスト通知を送信）
python run_phase1_demo_simple.py
```

### 3. 本番実行
```bash
# 強制実行（時刻に関係なく実行）
python run_phase1_production.py --force

# 定時実行（8:00, 15:00, 21:00のみ）
python run_phase1_production.py
```

### 4. Cron設定
```bash
# Cronジョブを自動設定
./setup_cron_phase1.sh
```

## 実装の特徴

### テスト駆動開発（TDD）
- 全ての機能に対してテストコードを先に作成
- 高いコードカバレッジと信頼性を実現

### モジュール設計
- `SignalGenerator`: シグナル生成ロジック
- `TradingViewAlertSystem`: 通知システム
- `PerformanceTracker`: パフォーマンス記録

### 拡張性
- Phase 2以降の機能追加を考慮した設計
- 既存システムに影響を与えない独立した実装

## 次のステップ（Phase 2）
- OANDA APIとの統合
- デモ口座での自動売買
- より高度なリスク管理機能

詳細は `auto_trading_implementation_plan.md` を参照してください。