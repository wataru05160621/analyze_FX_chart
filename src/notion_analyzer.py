"""
Notion用の詳細分析モジュール
Volmanメソッドに基づく完全な分析内容を生成
"""
import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class NotionAnalyzer:
    """Notion用の詳細分析を生成するクラス"""
    
    def __init__(self):
        pass
    
    def create_detailed_analysis(self, claude_analysis: str) -> str:
        """
        Claude分析をNotionA用の詳細版に拡張
        環境認識、ビルドアップ、ダマシの可能性などを含む
        """
        try:
            # 既存の分析から重要な情報を抽出
            extracted_data = self._extract_analysis_data(claude_analysis)
            
            # Notion用の詳細分析を構築
            detailed_analysis = self._build_detailed_analysis(claude_analysis, extracted_data)
            
            return detailed_analysis
            
        except Exception as e:
            logger.error(f"Notion分析生成エラー: {e}")
            return claude_analysis  # フォールバック
    
    def _extract_analysis_data(self, analysis: str) -> Dict[str, any]:
        """分析から重要データを抽出"""
        data = {
            'current_price': None,
            'ema_positions': {},
            'setup_quality': None,
            'entry_points': [],
            'risk_warnings': [],
            'buildups': [],
            'support_resistance': []
        }
        
        # 現在価格
        price_match = re.search(r'現在価格[：:]\s*([\d.]+)', analysis)
        if price_match:
            data['current_price'] = price_match.group(1)
        
        # EMA配列
        if "25EMA > 75EMA > 200EMA" in analysis:
            data['ema_positions']['trend'] = 'bullish'
        elif "25EMA < 75EMA < 200EMA" in analysis:
            data['ema_positions']['trend'] = 'bearish'
        else:
            data['ema_positions']['trend'] = 'mixed'
        
        # セットアップ品質
        if "⭐⭐⭐⭐⭐" in analysis:
            data['setup_quality'] = 5
        elif "⭐⭐⭐⭐" in analysis:
            data['setup_quality'] = 4
        elif "⭐⭐⭐" in analysis:
            data['setup_quality'] = 3
        
        # エントリーポイント抽出
        entry_matches = re.findall(r'エントリー[：:]\s*([\d.]+)', analysis)
        data['entry_points'] = entry_matches
        
        # ビルドアップ検出
        if "ビルドアップ" in analysis:
            buildup_sections = re.findall(r'ビルドアップ[^。]*。', analysis)
            data['buildups'] = buildup_sections[:3]  # 最大3つ
        
        return data
    
    def _build_detailed_analysis(self, original_analysis: str, extracted_data: Dict) -> str:
        """Notion用の詳細分析を構築"""
        
        notion_analysis = f"""# 📊 USD/JPY Volmanメソッド詳細分析

## 🎯 エグゼクティブサマリー

### 現在の状況
- **現在価格**: {extracted_data.get('current_price', 'N/A')}
- **トレンド方向**: {self._get_trend_description(extracted_data['ema_positions']['trend'])}
- **セットアップ品質**: {'⭐' * extracted_data.get('setup_quality', 3)} ({extracted_data.get('setup_quality', 'N/A')}/5)
- **推奨アクション**: {self._get_action_from_analysis(original_analysis)}

---

## 🌍 環境認識（Market Context）

### セッション分析
{self._generate_session_analysis()}

### ボラティリティ環境
{self._generate_volatility_analysis(original_analysis)}

### マクロ構造
{self._generate_macro_structure(original_analysis)}

---

## 📈 プライスアクション詳細

### ビルドアップ分析
{self._generate_buildup_analysis(original_analysis, extracted_data)}

### サポート・レジスタンス構造
{self._generate_sr_analysis(original_analysis)}

### 25EMA相互作用
{self._generate_ema_interaction(original_analysis)}

---

## ⚠️ リスク評価とダマシの可能性

### ティーズブレイク（ダマシ）の兆候
{self._generate_fake_breakout_analysis(original_analysis)}

### 潜在的リスク要因
{self._generate_risk_factors(original_analysis)}

### スキップ判断基準
{self._generate_skip_criteria(original_analysis)}

---

## 📋 トレードプラン詳細

### プライマリーセットアップ
{self._extract_primary_setup(original_analysis)}

### 代替シナリオ
{self._extract_alternative_scenarios(original_analysis)}

### エクジット戦略
{self._generate_exit_strategy(original_analysis)}

---

## 🔍 Volmanメソッド七原則の適用

{self._apply_volman_principles(original_analysis)}

---

## 📊 オリジナル分析（Claude 3.5 Sonnet）

{original_analysis}

---

## 📝 トレード記録用メモ

### エントリー前チェックリスト
- [ ] ATR ≥ 7pips
- [ ] スプレッド ≤ 2pips
- [ ] ニュース確認（前後10分）
- [ ] ビルドアップ明確
- [ ] 25EMAサポート/レジスタンス確認
- [ ] 20/10ブラケットオーダー設定準備

### 観察ポイント
- 次のビルドアップ形成予想レベル
- セッション移行時の注意点
- 重要経済指標の時間

### 学習ポイント
- 今回のセットアップから学んだこと
- 改善すべき分析ポイント
- 次回への課題

---

*分析日時: {self._get_current_time()}*
*分析手法: Bob Volman「Forex Price Action Scalping」*
*システム: Claude 3.5 Sonnet + Python自動分析*
"""
        
        return notion_analysis
    
    def _get_trend_description(self, trend: str) -> str:
        """トレンドの説明を生成"""
        descriptions = {
            'bullish': '📈 上昇トレンド（EMA完全上昇配列）',
            'bearish': '📉 下降トレンド（EMA完全下降配列）',
            'mixed': '📊 混在/レンジ（EMA配列不明確）'
        }
        return descriptions.get(trend, '不明')
    
    def _get_action_from_analysis(self, analysis: str) -> str:
        """分析から推奨アクションを抽出"""
        if "即時エントリー" in analysis:
            return "🟢 即時エントリー可能"
        elif "セットアップ待機" in analysis:
            return "🟡 セットアップ形成待ち"
        elif "トレード見送り" in analysis:
            return "🔴 本日トレード見送り"
        else:
            return "🟡 慎重に観察継続"
    
    def _generate_session_analysis(self) -> str:
        """セッション分析を生成"""
        from datetime import datetime
        current_hour = datetime.now().hour
        
        if 9 <= current_hour < 15:
            return """**アジアセッション中盤**
- 東京市場活発、実需フロー注視
- ボラティリティ: 中程度
- 注目: 日銀関連ニュース、中国指標"""
        elif 15 <= current_hour < 21:
            return """**ロンドンセッション序盤**
- 欧州勢参入でボラティリティ上昇
- トレンド発生の可能性高
- 注目: 欧州経済指標、ECB関連"""
        else:
            return """**NYセッション/アジア早朝**
- 米国指標の影響大
- 流動性変動に注意
- 注目: FOMC、米雇用統計"""
    
    def _generate_volatility_analysis(self, analysis: str) -> str:
        """ボラティリティ分析を生成"""
        if "ATR" in analysis:
            atr_match = re.search(r'ATR[：:]\s*([\d.]+)', analysis)
            if atr_match:
                atr = float(atr_match.group(1))
                if atr >= 10:
                    return f"**高ボラティリティ環境** (ATR: {atr}pips)\n- スキャルピング好機\n- ストップ幅調整推奨\n- ブレイクアウト期待大"
                elif atr >= 7:
                    return f"**適正ボラティリティ** (ATR: {atr}pips)\n- Volmanセットアップ有効\n- 20/10戦略適用可\n- 通常のリスク管理"
                else:
                    return f"**低ボラティリティ警告** (ATR: {atr}pips)\n- トレード回避推奨\n- ビルドアップ形成待ち\n- レンジトレード検討"
        
        return "**ボラティリティ評価**\n- ATR確認必須\n- 7pips以上でトレード可\n- セッション特性考慮"
    
    def _generate_macro_structure(self, analysis: str) -> str:
        """マクロ構造分析"""
        return """**日足/4時間足構造**
- 主要トレンド: 上位時間軸確認推奨
- 重要レベル: 前日高値/安値意識
- 週次ピボット: サポート/レジスタンスとして機能
- 月次レンジ: 大局的な方向性示唆"""
    
    def _generate_buildup_analysis(self, analysis: str, data: Dict) -> str:
        """ビルドアップ詳細分析"""
        buildup_text = "**現在のビルドアップ状況**\n\n"
        
        if data['buildups']:
            for i, buildup in enumerate(data['buildups'], 1):
                buildup_text += f"{i}. {buildup}\n"
        else:
            buildup_text += "- 明確なビルドアップ未形成\n"
            buildup_text += "- 価格圧縮の初期段階\n"
            buildup_text += "- 形成には更に時間必要\n"
        
        buildup_text += "\n**ビルドアップ品質評価**\n"
        buildup_text += "- 圧縮期間: 確認必要\n"
        buildup_text += "- パターン明確性: 評価中\n"
        buildup_text += "- ブレイク方向予測: トレンドフォロー優先\n"
        
        return buildup_text
    
    def _generate_sr_analysis(self, analysis: str) -> str:
        """サポート・レジスタンス分析"""
        # 分析から価格レベルを抽出
        price_levels = re.findall(r'(\d{3}\.\d{3})', analysis)
        
        sr_text = "**識別された重要レベル**\n\n"
        if price_levels:
            unique_levels = sorted(set(price_levels), reverse=True)[:5]
            for level in unique_levels:
                sr_text += f"- {level}: 潜在的S/Rゾーン\n"
        else:
            sr_text += "- 明確なレベル抽出中\n"
        
        sr_text += "\n**ラウンドナンバー**\n"
        sr_text += "- XX.000: 心理的節目（最重要）\n"
        sr_text += "- XX.500: 中間値（重要）\n"
        sr_text += "- XX.250/750: 四分値（注意）\n"
        
        return sr_text
    
    def _generate_ema_interaction(self, analysis: str) -> str:
        """EMA相互作用分析"""
        return """**25EMA動的サポート/レジスタンス**
- 価格との位置関係: タッチ回数確認
- 反発/突破パターン: 過去3回の反応
- EMA角度: トレンド強度の指標
- プルバック深度: 25EMAまでの戻りが理想

**複数EMA収束ゾーン**
- 25/75/200EMA接近時は大変動の前兆
- ゴールデン/デッドクロス監視
- EMAファンの拡大/収縮でトレンド判断"""
    
    def _generate_fake_breakout_analysis(self, analysis: str) -> str:
        """ダマシ分析"""
        return """**ティーズブレイク識別ポイント**
1. **出来高不足**: ブレイク時の勢い欠如
2. **即座の逆行**: 2-3本以内での反転
3. **ヒゲ形成**: 実体でのブレイク失敗
4. **サポレジ反発**: 重要レベルでの拒絶

**ダマシ回避策**
- ブレイク後の再テスト待ち（セットアップB）
- 実体2本確認ルール
- ニュース時間帯回避
- セッション開始30分は静観"""
    
    def _generate_risk_factors(self, analysis: str) -> str:
        """リスク要因分析"""
        return """**現在のリスク要因**
1. **市場リスク**
   - 予期せぬニュース発表
   - 中央銀行介入の可能性
   - 地政学的イベント

2. **テクニカルリスク**
   - 上位時間足との相違
   - 隠れたダイバージェンス
   - 流動性の枯渇

3. **執行リスク**
   - スリッページ拡大
   - 約定拒否の可能性
   - プラットフォーム障害"""
    
    def _generate_skip_criteria(self, analysis: str) -> str:
        """スキップ基準"""
        return """**Volmanスキップルール適用状況**
- ✓ ATR < 7pips → トレード禁止
- ✓ スプレッド > 2pips → 執行見送り
- ✓ ニュース前後10分 → 完全回避
- ✓ 不明瞭セットアップ → 見送り必須
- ✓ セッション移行期 → 要注意

**追加考慮事項**
- 金曜日午後のポジション調整
- 月初/月末のフロー
- 休場明けの乱高下"""
    
    def _extract_primary_setup(self, analysis: str) -> str:
        """プライマリーセットアップ抽出"""
        setup_section = ""
        
        # セットアップA-Fの検出
        setup_patterns = {
            'A': 'パターンブレイク',
            'B': 'パターンブレイクプルバック',
            'C': 'コームーブリバーサル',
            'D': 'フェイルドブレイクリバーサル',
            'E': 'セカンドブレイク',
            'F': 'レンジブレイク'
        }
        
        for key, name in setup_patterns.items():
            if f"セットアップ{key}" in analysis or name in analysis:
                setup_section += f"**セットアップ{key}: {name}**\n"
                setup_section += self._extract_setup_details(analysis, key)
                break
        
        if not setup_section:
            setup_section = "**セットアップ形成待ち**\n監視継続中"
        
        return setup_section
    
    def _extract_setup_details(self, analysis: str, setup_type: str) -> str:
        """セットアップ詳細抽出"""
        details = f"- タイプ: Volmanセットアップ{setup_type}\n"
        
        # エントリー価格
        entry_match = re.search(r'エントリー[：:]\s*([\d.]+)', analysis)
        if entry_match:
            details += f"- エントリー: {entry_match.group(1)}\n"
            details += f"- TP (+20pips): {float(entry_match.group(1)) + 0.200:.3f}\n"
            details += f"- SL (-10pips): {float(entry_match.group(1)) - 0.100:.3f}\n"
        
        details += "- R:R比: 2:1 (固定)\n"
        details += "- ポジションサイズ: 口座の1%リスク\n"
        
        return details
    
    def _extract_alternative_scenarios(self, analysis: str) -> str:
        """代替シナリオ抽出"""
        return """**シナリオB: 逆方向ブレイク**
- 条件: 現在のセットアップ失敗時
- 監視: 逆方向のビルドアップ形成
- 対応: セットアップD（フェイルドブレイク）

**シナリオC: レンジ継続**
- 条件: ブレイク失敗の繰り返し
- 監視: レンジ境界でのピンバー
- 対応: セットアップF（レンジトレード）"""
    
    def _generate_exit_strategy(self, analysis: str) -> str:
        """エクジット戦略"""
        return """**基本エクジット: 20/10ブラケット**
- TP: +20pips（機械的決済）
- SL: -10pips（例外なし）

**早期エクジット条件**
1. 逆方向の明確なセットアップ出現
2. ニュース発表5分前
3. スプレッド急拡大（3pips超）
4. 予期せぬボラティリティ急変

**利益最大化オプション**
- トレーリング不使用（Volman原則）
- 部分決済不採用（シンプル維持）
- 追加エントリー禁止（1トレード完結）"""
    
    def _apply_volman_principles(self, analysis: str) -> str:
        """Volman七原則の適用"""
        return """### 1. ダブルプレッシャー
- 現在の適用: 買い圧力と売り圧力の評価
- 観察ポイント: ビルドアップ内での力関係

### 2. ファーストブレイク
- 原則: 初回ブレイクへの素早い反応
- 注意: ティーズの可能性常に考慮

### 3. ブロック（抵抗帯）
- 識別: 複数回反発ゾーン
- 活用: ブレイク後の再テスト地点

### 4. コンボ（複合要因）
- 確認: 複数の根拠の重複
- 例: EMA + S/R + ビルドアップ

### 5. マグネット効果
- 観察: 価格が引き寄せられるレベル
- 活用: エントリー/エクジット計画

### 6. トレードユニット
- 固定: 常に同一リスク（1%）
- 調整: 口座残高に応じて自動計算

### 7. 情報階層
- 優先順位: プライスアクション > 指標 > ニュース
- 判断: 価格が全てを語る"""
    
    def _get_current_time(self) -> str:
        """現在時刻を取得"""
        from datetime import datetime
        return datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')