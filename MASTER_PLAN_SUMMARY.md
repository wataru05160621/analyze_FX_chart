# FX自動売買システム マスタープラン概要

## 🎯 最終目標
AWS SageMakerの機械学習による高期待値（プラスのエッジ）を持つ完全自動売買システム

## 📅 実装フェーズ

### Phase 1: アラートシステム（0-2ヶ月）✅ 実装済み
- TradingViewアラート生成
- Slack/メール通知
- 手動取引での検証
- **現在のステータス**: 完了

### Phase 2: API統合（2-4ヶ月）
- XMTrading MT5 API連携
- デモ口座での自動売買
- リスク管理システム
- パフォーマンス追跡

### Phase 3: AWS完全統合（4-6ヶ月）
- ECS Fargateでの24時間稼働
- 少額実取引開始（10万円）
- SageMaker機械学習の導入
- 継続学習システムの構築

### Phase 4: 本格運用（6ヶ月以降）
- 複数通貨ペア対応
- 投資額増額（100万円）
- 完全自動売買
- 期待値ベースの資金管理

## 🤖 SageMaker継続学習サイクル

### 初期段階（期待値の確立）
1. PDFの売買原則を基本モデルに実装
2. Claude APIでの分析結果を教師データとして蓄積
3. 24時間後の予測検証システム

### 成長段階（3-6ヶ月で期待値の最大化）
1. プラスの期待値を持つ取引パターンの学習
2. リスクリワード比の最適化（1:2以上）
3. 週次での増分学習
4. PDFルールとの整合性チェック
5. 期待値の継続的な改善

### コスト構造
- 初期構築: 約80,000円
- 月額運用: 2,900円〜（取引量により変動）
- ROI: 6ヶ月で初期投資回収見込み

## 📁 関連ドキュメント

### 実装計画
- `/auto_trading_implementation_plan.md` - 詳細な4フェーズ計画
- `/sagemaker_continuous_learning.md` - 機械学習の仕組み
- `/sagemaker_implementation_details.md` - 技術詳細

### 実装済みコード
- `/src/phase1_alert_system.py` - Phase 1実装
- `/src/tradingview_alert_generator.py` - アラート生成
- `/src/tradingview_webhook_handler.py` - Webhook処理

### 次期実装予定
- `/doc/phase2_xmtrading_plan.md` - XMTrading実装計画
- `/migration_plan.md` - API移行計画

## 🚀 次のアクション

1. **Phase 2の開始判断**
   - Phase 1での売買シグナル精度の確認
   - デモ口座の開設
   - MT5 Python APIのセットアップ

2. **SageMaker準備**
   - 教師データの蓄積継続
   - 初期モデルの設計
   - AWS環境の準備

3. **リスク管理**
   - 最大損失額の設定
   - ポジションサイズの自動計算
   - 緊急停止システムの実装

---
最終更新: 2025-01-09