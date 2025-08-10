# DAILY_STATS_JOB.md — 日次集計(23:45 JST)

## 目的
- 当日の各ページについて `AutoResult` を自動判定（TP/SL/Timeout/NoFill）。
- セットアップ別の勝率を Beta+EWMA で更新し、S3: `stats/setup_stats.json` に保存。

## 入力
- Notion DB: RunId, Date, pair, plan.tp/sl, entry方向
- TwelveData: エントリー以降の足（5m推奨）

## 判定ルール
- 先に到達した方を採用。同バー同時ヒットは SL を優先（保守）。
- Timeout: エントリー後90分 or セッション終了。

## 疑似コード
1. 当日のページを `Date` で検索
2. `AutoResult` 空のみ抽出
3. TwelveData から後続足を取得
4. TP/SL/Timeout 判定（スプレッド考慮）→ PnL_pips, R_multiple 算出
5. ページ更新（AutoResult, PnL_pips, R_multiple）
6. セットアップ別に W/L を集計 → Beta+EWMA → p_today
7. JSON を S3: `stats/setup_stats.json` に保存
