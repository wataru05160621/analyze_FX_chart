# SERENA MCP MEMORY — analyze_FX_chart (MVP)

> 目的：コンテキスト節約 & 一貫性維持（投資助言回避／期待値志向／25EMA/BBF/キリ番）。

## 行動原則
- 期待値で評価（勝率は二次）。トレンドフォロー優先。
- ビルドアップの質（幅≥10p・足≥10・25EMA内包）と根拠3つ以上の重複。
- 20/10 ブラケット基準（ATRで±25%調整）。ニュース±10分除外、スプレッド>2p除外、ATR20<7p除外。
- 25EMA傾きとBBF（Build‑Up→Break→Follow‑Through）。キリ番を磁石として扱う。
- 禁止: 断定的・勧誘的な投資助言表現。

## セットアップ（6型）
A: Pattern Break／B: PB Pullback／C: Probe Rev.／D: Failed Break Rev.／E: Momentum Cont.／F: Range Scalp

## データソースとチャート
- 価格データは **TwelveData API** を使用（yfinance禁止）。
- 分析は **5分足と1時間足** の両方を生成・参照し、Notionにはチャート画像も添付する。

## 見送り基準
- ATR20<7p、スプレッド>2p、ニュース±10分、ビルドアップ基準未満（3条件のうち2未満）
- 連敗3回 or 日次-2R 到達 → 30分クールダウン

## チェックリスト
- EMA傾き／Build‑Up（幅/足/EMA内包）／ブレイク実体≥枠幅×0.2／FT確認／キリ番距離≥8p／20/10設置／見送り最終確認
