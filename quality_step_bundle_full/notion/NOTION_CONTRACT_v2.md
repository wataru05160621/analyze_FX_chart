# NOTION_CONTRACT_v2.md — DB拡張と本文テンプレ

## 新規プロパティ
- ConfluenceCount (number)
- NoTradeReason (multi_select: ATR<7, Spread>2, NewsWindow, BuildUpWeak, Other)
- AdviceFlags (multi_select)
- Env_1hTrend (select: Up/Down/Range)
- BuildUpQuality (select: Strong/Normal/Weak)
- RunId (rich_text, unique)
- AutoResult (select: TP/SL/Timeout/NoFill)
- ManualOverride (checkbox), ManualResult (select)
- PnL_pips (number), R_multiple (number)
- EngineVersion (text), PromptHash (text), DataSource (text)

## 追加API例（プロパティ追加）
```bash
curl -X PATCH https://api.notion.com/v1/databases/{DB_ID}  -H "Authorization: Bearer $NOTION_API_KEY"  -H "Notion-Version: 2022-06-28" -H "Content-Type: application/json"  --data '{
  "properties": {
    "ConfluenceCount": {"number":{}},
    "NoTradeReason": {"multi_select":{"options":[
      {"name":"ATR<7"},{"name":"Spread>2"},{"name":"NewsWindow"},{"name":"BuildUpWeak"},{"name":"Other"}]}},
    "AdviceFlags": {"multi_select":{}},
    "Env_1hTrend": {"select":{"options":[{"name":"Up"},{"name":"Down"},{"name":"Range"}]}},
    "BuildUpQuality": {"select":{"options":[{"name":"Strong"},{"name":"Normal"},{"name":"Weak"}]}},
    "RunId":{"rich_text":{}},
    "AutoResult":{"select":{"options":[{"name":"TP"},{"name":"SL"},{"name":"Timeout"},{"name":"NoFill"}]}},
    "ManualOverride":{"checkbox":{}},
    "ManualResult":{"select":{"options":[{"name":"TP"},{"name":"SL"},{"name":"Timeout"},{"name":"NoFill"}]}},
    "PnL_pips":{"number":{}},
    "R_multiple":{"number":{}},
    "EngineVersion":{"rich_text":{}},
    "PromptHash":{"rich_text":{}},
    "DataSource":{"rich_text":{}}
  }
 }'
```

## 本文テンプレ（4ブロック + Features）
- 見出し: `{pair} {tf} — Setup {A..F or No-Trade}`
- 環境認識（1h）
- セットアップ根拠（5m）
- 計画（Entry/TP/SL/Timeout）
- 示唆（No-Trade理由 or 注意点）
- **Features(JSON) コードブロック**（分析に使った材料をそのまま出力）
