# CLAUDE_NEXT_STEP.md — 品質向上ステップ（確定）

## ゴール
- Notionを「真実のソース」化：**文章＋JSON＋5m/1h画像**を毎回固定構造で保存。
- 可読性より**根拠材料**を優先：本文末に Features(JSON) を必ず添付。
- 勝率は**自動評価**を一次。必要時のみ ManualOverride。翌日の EV に反映。

## スプリント計画（2週）
- Sprint 1（P0 品質強化）: Q01〜Q06
- Sprint 2（P1 可視化/外部発信）: Q07〜Q09

## タスク
Q01. 分析ゲート強化（Gate→Decide→Explain）  
- Gate: ATR<7p / Spread>2 / News±10m / BuildUp 2/3未満 → No-Trade（理由を出力）
- Decide: 1h EMA傾きで環境→5m決定木（A〜F）
- Explain: rationale≥3、confluence_countを算出

Q02. EV計算モジュール  
- Beta(α0,β0)+EWMAでセットアップ別勝率 p_today を更新
- ev_R = p_today * (TP/SL) - (1 - p_today) * 1.0
- confluence低時の減衰係数(0.8)を適用可

Q03. 言語ガード（助言回避）  
- guards/LINGUISTIC_GUARD.yaml に禁句と置換マップ
- 出力直前に検閲、ヒットは advice_flags に記録

Q04. Notion本文テンプレと新規プロパティ  
- 4ブロック（環境/根拠/計画/示唆）＋ 画像2枚（5m/1h）
- 本文末に Features(JSON) をコードブロックで貼付
- 追加: ConfluenceCount, NoTradeReason[], AdviceFlags[], Env_1hTrend, BuildUpQuality, RunId, AutoResult, ManualOverride, ManualResult, PnL_pips, R_multiple, EngineVersion, PromptHash, DataSource

Q05. Slack Blocks テンプレ（成功/失敗/No-Trade）  
- 120字以内の要約＋Notionリンク。失敗はフェーズ名・再試行方針を表示

Q06. スキーマ拡張＆検証  
- schema/analysis_output.schema.json を更新（confluence_count, no_trade_reasons[], advice_flags[]）
- 検証NG→Slack :warning: & no-trade でフォールバック

Q07. ヘルスチェック（P1）  
- /health（または Slack `/fx status`）: last_success_ts / last_run_id / error_counts

Q08. Run Once（P1）  
- Slack Slash or CLI: Dry-run（Notion下書き）/ 本番 / Retry last-run

Q09. 外部出力（P1）  
- X: テンプレ固定・禁句ガード・5m画像1枚・WP記事リンク。自動投稿は閾値を満たす場合のみ
- WordPress: ドラフトのみ、学習ノート＋内部記事リンク、画像はWPメディアにアップ

## Exit
- 文章: 8–12行 + Features(JSON)、助言回避
- JSON: schema100%・charts(5m/1h)・ev_R・confluence_count
- Notion: 本文＋画像2枚＋新プロパティ反映
- Slack: 全ジョブ通知、No-Trade理由テンプレ一致
- 安定性: 5営業日連続で欠損0・重複0、自動再試行で70%自己回復
