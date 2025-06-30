"""
Claude 3.5 Sonnet を使用したFXチャート分析モジュール
"""
import base64
import logging
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic
from .config import CLAUDE_API_KEY
from .pdf_extractor import PDFExtractor

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
        """プライスアクションの原則.pdfの内容を読み込み"""
        try:
            pdf_path = Path(__file__).parent.parent / "doc" / "プライスアクションの原則.pdf"
            if pdf_path.exists():
                logger.info("プライスアクションの原則.pdfを読み込み中...")
                pdf_extractor = PDFExtractor(pdf_path)
                self.book_content = pdf_extractor.extract_text()
                logger.info(f"PDFコンテンツ読み込み完了: {len(self.book_content)}文字")
            else:
                logger.warning(f"PDFファイルが見つかりません: {pdf_path}")
                self.book_content = ""
        except Exception as e:
            logger.error(f"PDF読み込みエラー: {e}")
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
        """テキストベースの分析用プロンプトを作成"""
        book_excerpt = self.book_content[:80000] if self.book_content else ""
        
        return f"""あなたは経験豊富なFXトレーダーおよびテクニカル分析の専門家です。以下の参考書籍「プライスアクションの原則」の内容に基づいて、提供された市場データを詳細に分析してください。

# 参考書籍: プライスアクションの原則（重要部分の抜粋）
{book_excerpt}

# 市場データ:
{market_context}

# 分析要件:

## 1. 現在の市場状況の確認
- 通貨ペアと現在価格の認識
- 移動平均線との関係分析
- RSIとMACDの状況評価

## 2. テクニカル分析
- 価格と移動平均線の位置関係から読み取れるトレンド方向
- オシレーターの状況から判断される市場の過熱感
- 主要なサポート・レジスタンスレベルの特定

## 3. トレードシナリオ
### A. 上昇シナリオ（確率: X%）
- エントリーポイント: [価格]
- ターゲット: [価格]
- ストップロス: [価格]
- 根拠: [プライスアクション理論に基づく説明]

### B. 下降シナリオ（確率: Y%）
- エントリーポイント: [価格]
- ターゲット: [価格]
- ストップロス: [価格]
- 根拠: [プライスアクション理論に基づく説明]

## 4. リスク管理
- ポジションサイジングの推奨
- 市場環境を考慮したリスク要因
- 注意すべき経済指標やイベント

## 5. 結論
- 推奨アクション（買い/売り/待機）
- 根拠の要約
- 今後の注目ポイント

分析は必ず日本語で、具体的な価格レベルを含めて回答してください。"""

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
        """分析用プロンプトを作成"""
        # PDFコンテンツを適切な長さに制限（約80,000文字）
        book_excerpt = self.book_content[:80000] if self.book_content else ""
        
        return f"""あなたは経験豊富なFXトレーダーおよびテクニカル分析の専門家です。以下の参考書籍「プライスアクションの原則」の内容に基づいて、提供されたチャート画像を詳細に分析してください。

# 参考書籍: プライスアクションの原則（重要部分の抜粋）
{book_excerpt}

# チャート分析要件:

## 1. 初期設定の確認
- 通貨ペア、時間足の特定
- 現在時刻の記録（日本時間）
- 3本の移動平均線の識別: 25MA（緑）、75MA（黄）、200MA（赤）
- 現在価格と各MAの値を記録

## 2. 市場構造分析

### A. チャート概観
- チャートに見える全体的な価格動向を説明
- 主要なスイングハイ・ローを具体的な価格レベルで特定
- チャートパターン（三角保ち合い、フラッグ、ヘッドアンドショルダー等）の識別
- 現在の市場フェーズ（トレンド、レンジ、ブレイクアウト等）の判定

### B. 移動平均線分析
- 現在のMA位置と価格との関係（上/下）
- 各MAの傾き（上昇、下降、横ばい）とその示唆
- 最近のクロスオーバー（ゴールデンクロス、デッドクロス）
- MA間の距離（収束、拡散、スクイーズ）
- 価格と各MAの相互作用（サポート、レジスタンス、マグネット効果）

### C. サポート・レジスタンスレベル
以下の形式で表を作成:
| レベル種別 | 価格帯 | 根拠 |
|------------|--------|------|
| S1 | [価格] | [理由 - 例: 前回安値、MAサポート] |
| S2 | [価格] | [理由] |
| R1 | [価格] | [理由] |
| R2 | [価格] | [理由] |

## 3. マルチタイムフレーム分析
- 現在の時間足を上位時間足と関連付け
- 現在の動きが大きなトレンドと一致/相反しているか確認
- 時間足間のダイバージェンスを指摘

## 4. トレードシナリオ
確率加重を含む2つのシナリオを提供:

### シナリオA: [強気/弱気] (XX%の確率)
**エントリー条件:**
- 必要な具体的プライスアクションシグナル
- 確認のために必要なMAの挙動
- ローソク足パターン（ピンバー、エンガルフィング等）

**トレード詳細:**
- エントリー: [具体的な価格または条件]
- ストップロス: [価格と根拠]
- 利益確定1: [価格]（部分決済）
- 利益確定2: [価格]（最終目標）
- リスクリワード比: [計算結果]
- ポジションサイズ: [推奨される口座の%]

### シナリオB: [反対方向] (XX%の確率)
[シナリオAと同じ形式]

## 5. リスク要因と市場考慮事項
- 今後の経済指標発表や市場オープン時間
- 相関リスク（ドルインデックス、債券、株式）
- セッション別リスク（東京/ロンドン/ニューヨーク）
- 流動性の考慮
- ダマシのブレイクアウトリスク

## 6. 実行ガイドライン
- 市場セッションに基づく最適なエントリータイミング
- ポジションへの段階的エントリー方法
- ストップロスを建値に移動するタイミング
- 部分利益確定戦略
- デイトレードの最大保有期間

## 7. 要約アクションプラン
以下の簡潔な箇条書きリストを提供:
- 注視すべき主要なトレードセットアップ
- 分析を無効にする重要レベル
- リスク管理ルール
- 次回の見直し時刻

## 分析スタイルガイドライン:
1. 概算ではなく正確な価格レベルを使用
2. 各観察の「理由」を説明
3. テクニカル分析と実践的なトレード考慮事項のバランス
4. 価格動向を議論する際は具体的な時間参照を含める
5. 不確実性と代替シナリオを認識
6. 良好なリスクリワードを持つ高確率セットアップに焦点
7. プロフェッショナルでありながらアクセスしやすいトーンで記述
8. 明確性のためマークダウン形式を使用
9. 関連するプライスアクション用語を含める
10. 常に潜在的利益よりも資本保全を優先

## 重要な分析原則:
書籍「プライスアクションの原則」の考え方に基づき、以下の要素を必ず分析に組み込んでください（引用は不要、概念の適用のみ）：

1. **ダブルの圧力**: 同じ方向への2つの圧力が重なる状況を特定
2. **ビルドアップ**: ブレイク前の価格の圧縮・蓄積を観察
3. **ダマシのブレイク/高値/安値**: 偽のブレイクアウトパターンを識別
4. **切りの良い数字**: 心理的節目（.00、.50等）のマグネット効果
5. **スクイーズ**: MAとパターンラインに挟まれた価格の圧縮
6. **アーチパターン**: 連続する高値/安値の形状分析
7. **20ピップス利確/10ピップス損切り**: 基本的なリスク管理
8. **支配的な圧力の方向**: 優勢な側についてトレード
9. **パターンラインとMAの相互作用**: 動的サポート/レジスタンス
10. **マルチプルタッチ**: 同じレベルでの複数回の反発/反落

これらの概念を自然に分析に織り込み、実践的なトレードプランを構築してください。"""
    
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
            
            # Claude APIを呼び出し
            logger.info("Claude APIに分析を依頼中...")
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