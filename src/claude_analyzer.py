"""
Claude 3.5 Sonnet を使用したFXチャート分析モジュール
"""
import base64
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic
from .config import CLAUDE_API_KEY

# Lambda環境以外でのみPDFExtractorをインポート
if not os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    try:
        from .pdf_extractor import PDFExtractor
    except ImportError:
        PDFExtractor = None
else:
    PDFExtractor = None

logger = logging.getLogger(__name__)

class ClaudeAnalyzer:
    """Claude 3.5 Sonnet でチャート分析を行うクラス"""
    
    def __init__(self):
        if not CLAUDE_API_KEY or CLAUDE_API_KEY == "your_claude_api_key_here":
            raise ValueError("CLAUDE_API_KEYが設定されていません")
        
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        self.book_content = None
        
        # プライスアクションの原則.pdfを読み込み
        self._load_book_content()
    
    def _load_book_content(self):
        """プライスアクションの原則のマークダウンファイルを読み込み"""
        try:
            # マークダウンファイルのディレクトリ
            md_dir = Path(__file__).parent.parent / "doc" / "プライスアクションの原則"
            
            if md_dir.exists():
                logger.info("プライスアクションの原則のマークダウンファイルを読み込み中...")
                
                # 読み込み順序を定義
                file_order = [
                    "fx_scalping_blog_outline.md",
                    "chapter_2_deepdive.md", 
                    "chapter_3_deepdive.md",
                    "chapter_4_deepdive.md",
                    "chapter_5_deepdive.md",
                    "chapter_9_deepdive.md"
                ]
                
                content_parts = []
                for filename in file_order:
                    file_path = md_dir / filename
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content_parts.append(f"### {filename}\n{f.read()}\n\n")
                            logger.info(f"{filename}を読み込みました")
                
                self.book_content = "\n".join(content_parts)
                logger.info(f"プライスアクション原則コンテンツ読み込み完了: {len(self.book_content)}文字")
            else:
                # Lambda環境ではPDF読み込みをスキップ
                if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
                    logger.info("Lambda環境のため、PDFコンテンツをスキップします")
                    self.book_content = "# Volmanメソッドベースの分析\n\nVolmanメソッドに基づいた価格アクション分析を実行します。"
                else:
                    # 既存のPDF読み込み処理にフォールバック
                    pdf_path = Path(__file__).parent.parent / "doc" / "プライスアクションの原則.pdf"
                    if pdf_path.exists() and PDFExtractor:
                        logger.info("プライスアクションの原則.pdfを読み込み中...")
                        pdf_extractor = PDFExtractor(pdf_path)
                        self.book_content = pdf_extractor.extract_text()
                        logger.info(f"PDFコンテンツ読み込み完了: {len(self.book_content)}文字")
                    else:
                        if not PDFExtractor:
                            logger.warning("PDFExtractorが利用できません")
                        else:
                            logger.warning(f"PDFファイルが見つかりません: {pdf_path}")
                        self.book_content = ""
        except Exception as e:
            logger.error(f"コンテンツ読み込みエラー: {e}")
            self.book_content = ""
    
    def _encode_image(self, image_path: str) -> str:
        """画像をbase64エンコード"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"画像エンコードエラー: {e}")
            raise
    
    def _create_text_analysis_prompt(self, market_context: str) -> str:
        """テキストベースの分析用プロンプトを作成（Volmanメソッド準拠）"""
        book_excerpt = self.book_content[:80000] if self.book_content else ""
        
        return f"""あなたはBob Volmanの「Forex Price Action Scalping」メソッドを完全に理解したFXスキャルピング専門家です。以下のVolmanメソッドのマークダウンファイル内容に基づいて、USD/JPY 5分足チャートの分析を行ってください。

# Volmanメソッド参考資料:
{book_excerpt}

# 市場データ:
{market_context}

# Volmanメソッドに基づく分析要件:

## 1. 現在の市場状況の確認
- USD/JPY価格と25EMAとの関係（Volman唯一の指標）
- 現在のセッション（アジア/欧州/米国）とボラティリティ
- 直近のビルドアップまたは価格圧縮の有無

## 2. プライスアクション7原則の適用
1. **ダブルプレッシャー**: 現在観察される買い/売り圧力の重複
2. **サポート/レジスタンスゾーン**: 重要な価格帯の特定
3. **ビルドアップ**: 現在形成中または完成したビルドアップ
4. **ティーズブレイク**: フェイクアウトの兆候
5. **プルバックリバーサル**: トレンド継続の可能性
6. **高値/安値のプローブ**: 極値テストの状況
7. **ラウンドナンバー**: 00/50レベルの影響

## 3. Volmanセットアップの識別
現在のチャートで適用可能なセットアップ（A-F）:
- **パターンブレイク（A）**: ビルドアップからの初回ブレイク
- **パターンブレイクプルバック（B）**: リテスト後のエントリー
- **プローブリバーサル（C）**: 極値での反転機会
- **フェイルドブレイクリバーサル（D）**: トラップされたポジション
- **モメンタム継続（E）**: 強いトレンド中のエントリー
- **レンジスキャルプ（F）**: レンジ内の短期トレード

## 4. 20/10ブラケットオーダー戦略
### エントリー候補1:
- セットアップタイプ: [A-Fから選択]
- エントリー価格: [具体的価格]
- 利益確定: +20pips = [価格]
- ストップロス: -10pips = [価格]
- 根拠: [Volman理論に基づく説明]

### エントリー候補2（もしあれば）:
[同様の形式]

## 5. スキップ判断基準
以下の条件に該当する場合はトレードを見送り:
- ATR < 7pips（ボラティリティ不足）
- スプレッド > 2pips
- ニュース前後±10分
- 不明瞭なビルドアップ
- セッション移行期

## 6. 推奨アクション
- **即時エントリー** / **セットアップ待機** / **本日トレード見送り**
- 理由: [Volmanメソッドに基づく明確な根拠]
- 次の注目時間: [具体的な時間帯]

分析は必ず日本語で、USD/JPYの具体的な価格レベル（小数点以下3桁）を含めて回答してください。"""

    async def analyze_text(self, market_context: str) -> str:
        """
        テキストベースの市場分析を実行
        """
        try:
            from .error_handler import AnalysisError
            
            prompt = self._create_text_analysis_prompt(market_context)
            
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            analysis = response.content[0].text
            logger.info(f"Claude分析完了: {len(analysis)}文字")
            return analysis
            
        except Exception as e:
            logger.error(f"Claude分析エラー: {e}")
            raise AnalysisError(f"Claude分析に失敗しました: {str(e)}")

    def _create_analysis_prompt(self) -> str:
        """分析用プロンプトを作成（Volmanスキャルピングメソッド準拠）"""
        # マークダウンコンテンツを適切な長さに制限（約80,000文字）
        book_excerpt = self.book_content[:80000] if self.book_content else ""
        
        return f"""あなたはBob Volmanの「Forex Price Action Scalping」メソッドを完全にマスターしたスキャルピング専門家です。以下のVolmanメソッドの詳細な解説に基づいて、提供されたUSD/JPY 5分足チャート画像を分析してください。

# Volmanスキャルピングメソッド完全ガイド:
{book_excerpt}

# Volmanメソッドによるチャート分析要件:

## 1. 基本情報の確認
- USD/JPY 5分足チャートの確認
- 現在時刻とセッション（アジア/欧州/米国）の特定
- 25EMA（Volman唯一の使用指標）の位置と傾き
- 現在価格: XXX.XXX形式で記録

## 2. Volman市場構造分析

### A. プライスアクション概観
- 直近3-4時間の価格動向とモメンタム
- スイングポイント（高値・安値）の明確な特定
- ビルドアップ形成の有無と質の評価
- BBFモデル（Build-up→Break→Follow-through）の段階

### B. 25EMA分析（Volman基準）
- 価格と25EMAの位置関係（トレンドバイアス）
- 25EMAの角度（急/緩/横ばい）
- 価格が25EMAをテストした回数と反応
- 25EMA周辺でのビルドアップ形成

### C. Volmanビルドアップ分析（最重要項目）
**現在のビルドアップ状況の特定:**
- 価格圧縮パターンの識別: 
  - 三角保ち合い、フラッグ、ペナント等のビルドアップ形状
  - ローソク足の実体とヒゲの縮小傾向
  - 高値切り下げ・安値切り上げの収束パターン
- ビルドアップ期間の測定:
  - 圧縮開始からの時間経過（○時間、○日間）
  - 過去の類似パターンとの比較
  - 圧縮度合いの定量化（価格幅の縮小率）
- 移動平均線との関係性:
  - EMAライン周辺での価格の挟み込み
  - EMA収束による圧力の蓄積
  - 複数EMAによる上下限定的な値動き

**ビルドアップの質的評価:**
- 質の高いビルドアップの条件:
  - 明確な方向性を持つトレンドからの一時的な調整
  - 十分な期間（通常3-8時間/5-20本程度）の価格圧縮
  - 出来高の減少傾向（可能な場合）
  - 複数のテクニカル要因による同一レベルでの反発
- 質の低いビルドアップの警告:
  - 方向感のないランダムな動き
  - 過度に長期間の圧縮（エネルギー散逸）
  - 主要サポレジを伴わない浮遊的な値動き

**今後のビルドアップ形成予測:**
- 潜在的ビルドアップレベルの特定:
  - 主要サポート・レジスタンスでのビルドアップ候補地点
  - フィボナッチレベル（23.6%, 38.2%, 50%, 61.8%）
  - 心理的節目（.00, .50等）でのビルドアップ可能性
  - 前回高値・安値でのビルドアップ形成予測
- ビルドアップ形成に必要な条件:
  - 到達予想時間と価格レベル
  - 形成に必要な市場環境（ボラティリティ、流動性）
  - 阻害要因（経済指標発表、セッション変更等）
- ブレイクアウト方向の事前予測:
  - 上位時間軸のトレンド方向との整合性
  - 建玉状況や市場センチメント
  - テクニカル指標の先行シグナル

### D. サポート・レジスタンスレベル
以下の形式で表を作成:
| レベル種別 | 価格帯 | 根拠 |
|------------|--------|------|
| S1 | [価格] | [理由 - 例: 前回安値、MAサポート] |
| S2 | [価格] | [理由] |
| R1 | [価格] | [理由] |
| R2 | [価格] | [理由] |

## 3. セッション別ボラティリティ分析
- 現在のセッション特性（アジア：低ボラ、欧州/米国：高ボラ）
- ATR値の確認（7pips以上でトレード可能）
- セッション移行期のリスク評価
- 主要な経済指標発表の有無（±10分はトレード禁止）

## 4. Volmanセットアップ識別とトレードプラン

### セットアップA: パターンブレイク（該当する場合）
**ビルドアップ評価（Volman基準）:**
- 圧縮期間: [X本のローソク足]
- 高値/安値の収束: [明確/不明確]
- 25EMAとの関係: [上/下/接触]
- ブレイク方向予測: [上/下] - 根拠: [ダブルプレッシャー等]

**エントリー条件（Volman基準）:**
- ビルドアップの明確なブレイク（実体での抜け）
- ブレイクキャンドルのサイズ（通常の1.5倍以上）
- 25EMAサポート/レジスタンスの確認
- ティーズブレイク（だまし）でないことの確認

**20/10ブラケットオーダー詳細:**
- エントリー: XXX.XXX
- 利益確定（TP）: エントリー +20pips = XXX.XXX
- ストップロス（SL）: エントリー -10pips = XXX.XXX
- リスクリワード比: 2:1（固定）
- ポジションサイズ: 口座の1%リスク
- OCOオーダー設定: 即座に設定

### その他の該当セットアップ（B-F）:
[各セットアップについて、該当する場合のみ記載]
- セットアップタイプと根拠
- エントリー/TP/SL価格
- 注意点

### スキップ判断（Volman No-Tradeルール）
以下の条件でトレード見送り:
- [ ] ATR < 7pips
- [ ] スプレッド > 2pips  
- [ ] ニュース前後10分以内
- [ ] 不明瞭なセットアップ
- [ ] セッション移行期

### 【必須】現在のセットアップ品質評価（5段階）
**重要: 必ずこの評価を実施し、星印で表示してください。**

**現在のビルドアップ状況評価:**
- ⭐️⭐️⭐️⭐️⭐️ (完璧): EMA完全収束、価格完全安定、十分な期間、明確なブレイクライン、**EMAトレンドフォロー条件完全満足**
- ⭐️⭐️⭐️⭐️☆ (優秀): EMA収束進行、価格圧縮継続、ブレイクライン明確、**EMAトレンドフォロー条件概ね満足**
- ⭐️⭐️⭐️☆☆ (普通): EMA接近、価格やや安定、形成中段階、**EMAトレンドフォロー条件部分的満足**
- ⭐️⭐️☆☆☆ (弱い): EMA部分的収束、価格不安定、初期段階、**EMAトレンドフォロー条件不十分**
- ⭐️☆☆☆☆ (不十分): ビルドアップと言えない、ランダム動き、**EMAトレンドフォロー条件未満足**

**EMAトレンドフォロー条件評価基準:**
- **完全満足**: 25EMA > 75EMA > 200EMA（上昇トレンド）または 25EMA < 75EMA < 200EMA（下降トレンド）
- **概ね満足**: 一部EMAクロスがあるが、主要トレンド方向は明確
- **部分的満足**: EMA配列は混在だが、価格位置でトレンド方向が読み取れる
- **不十分**: EMA配列が混乱、トレンド方向不明確
- **未満足**: EMAが完全に絡み合い、トレンドフォロー不可能

**現在の評価:** [⭐️で表示]
**EMAトレンドフォロー状況:** [完全満足/概ね満足/部分的満足/不十分/未満足]
**EMA配列:** [25EMA/75EMA/200EMAの位置関係を記載]
**評価根拠:** [ビルドアップの質とトレンドフォロー適合性の両面から記載]

## 5. Volmanリスク管理基準
- 経済指標発表スケジュール（±10分はトレード禁止）
- セッション別リスク評価
- スプレッドチェック（2pips以下が必須）
- ティーズブレイク（だまし）リスク

## 6. Volman実行チェックリスト
- [ ] ATR ≥ 7pips
- [ ] スプレッド ≤ 2pips
- [ ] ニュース時間を確認
- [ ] 明確なセットアップあり
- [ ] 20/10ブラケットオーダー設定準備OK

## 7. 【必須】Volmanセットアップ総合評価表

| 項目 | 内容 | 詳細 |
|------|------|------|
| **現在のセットアップ** | [A-F/なし] | [セットアップ名] |
| **ビルドアップ状況** | [完成/形成中/なし] | [圧縮期間、パターン] |
| **25EMAとの関係** | [上/下/接触] | [傾き、反応] |
| **エントリー価格** | XXX.XXX | [条件] |
| **TP (+20pips)** | XXX.XXX | [固定] |
| **SL (-10pips)** | XXX.XXX | [固定] |
| **ATR値** | XXpips | [7pips以上必須] |
| **スプレッド** | X.Xpips | [2pips以下必須] |
| **スキップ理由** | [該当項目] | [具体的理由] |

## 8. Volmanアクションプラン
- **推奨アクション**: [即時エントリー/セットアップ待機/トレード見送り]
- **主な根拠**: [Volmanセットアップ基準に基づく]
- **次の確認時間**: [具体的時間]
- **監視ポイント**: [価格レベル、ビルドアップ形成]
- **リスク警告**: [ニュース時間、スプレッド拡大等]

## Volman分析スタイル:
1. USD/JPYの正確な価格（小数点以下3桁）
2. 20/10ブラケットオーダーの厳守
3. スキップルールの徹底
4. セットアップA-Fの明確な識別
5. 25EMA以外の指標は使用しない

## Volmanメソッド七原則:
1. **ダブルプレッシャー**: 買い圧力と売り圧力の重複
2. **サポート/レジスタンスゾーン**: 価格帯としての認識
3. **ビルドアップ・ブレイクアウト**: エネルギー蓄積と解放
4. **ティーズブレイク**: ダマシの判別
5. **プルバックリバーサル**: 一時的調整からの継続
6. **プローブ**: 極値のテスト
7. **ラウンドナンバー**: 心理的節目の影響

## Volman実践ノート:
- 固定リスク/リワード比2:1の厳守
- ATR最低7pipsの確認  
- スプレッド2pips以下の確認
- ニュース前後10分のトレード禁止
- セットアップ不明瞭時は必ずスキップ

## 【重要】必須出力要件
分析結果には以下を必ず含めてください:
1. **Volmanセットアップ総合評価表** (表形式で必須項目を分析)
2. **セットアップ品質評価** (⭐️で5段階評価)
3. **20/10ブラケットオーダー詳細** (エントリー/TP/SL価格)
4. **スキップ判断チェックリスト** (全条件の確認)
5. **推奨アクション** (即時エントリー/待機/見送り)

分析は日本語で記述し、USD/JPY価格は必ずXXX.XXX形式（小数点以下3桁）で表現してください。"""
    
    def analyze_charts(self, chart_images: Dict[str, Path]) -> str:
        """チャート画像を分析"""
        try:
            logger.info("Claude 3.5 Sonnet でチャート分析を開始...")
            
            # プロンプトを準備
            prompt = self._create_analysis_prompt()
            
            # メッセージの内容を構築
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
            
            # 各チャート画像を追加
            for timeframe, image_path in chart_images.items():
                logger.info(f"{timeframe}チャートを追加中...")
                
                # 画像をエンコード
                image_data = self._encode_image(str(image_path))
                
                # 画像の説明テキストを追加
                content.append({
                    "type": "text", 
                    "text": f"\n\n## {timeframe.upper()}チャート (USD/JPY):"
                })
                
                # 画像を追加
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                })
            
            # Claude APIを呼び出し（リトライ付き）
            logger.info("Claude APIに分析を依頼中...")
            
            import time
            from anthropic import RateLimitError, APIStatusError
            
            max_retries = 5
            retry_delay = 60  # 60秒待機
            
            for attempt in range(max_retries):
                try:
                    response = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4000,
                        temperature=0.1,
                        messages=[
                            {
                                "role": "user",
                                "content": content
                            }
                        ]
                    )
                    break  # 成功したらループを抜ける
                    
                except (RateLimitError, APIStatusError) as e:
                    if hasattr(e, 'status_code') and e.status_code == 529:  # Overloaded
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)  # 段階的に待機時間を増やす
                            logger.warning(f"APIオーバーロード。{wait_time}秒待機してリトライ... (試行 {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                    logger.error(f"API呼び出しエラー: {e}")
                    raise
                except Exception as e:
                    logger.error(f"予期しないエラー: {e}")
                    raise
            else:
                # すべてのリトライが失敗した場合
                raise Exception(f"Claude APIが{max_retries}回の試行後もオーバーロード状態です")
            
            # 応答を取得
            analysis_result = response.content[0].text
            logger.info(f"Claude分析完了: {len(analysis_result)}文字")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Claude分析エラー: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, str]:
        """使用モデル情報を取得"""
        return {
            "provider": "Anthropic",
            "model": "Claude 3.5 Sonnet",
            "version": "claude-3-5-sonnet-20241022",
            "context_length": "200K tokens",
            "capabilities": "Vision, PDF processing, Financial analysis"
        }