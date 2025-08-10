# ANALYSIS SPEC — ルールと優先順位

## 環境判定（1h）
- EMA25傾き >= +30° 上、<= -30° 下、|傾き| < 10° レンジ

## Build-Up基準（5m）
- 幅≥10p / 足≥10 / 25EMA内包 の 2/3 以上

## ゲート
- ATR20<7p or Spread>2 or News±10m or BuildUp不足 → No-Trade

## セットアップ要約
- A: Break 実体≥枠幅×0.25、RN距離≥8p
- B: 一次Break後5本以内リテスト反転
- C: 天底ヒゲ抜け（≥8p）＋出来高増（低ロット）
- D: 失敗Break→逆方向エンゴルフ
- E: slope≥35° & ATR≥1.3×平均、Inside→Break
- F: 低ボラのレンジ内で +8〜10p
