"""
学習データ収集モジュール
既存の運用に影響を与えずにバックグラウンドでデータを収集
"""
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import boto3
from .logger import setup_logger

logger = setup_logger(__name__)

class TrainingDataCollector:
    """学習データを自動収集するクラス"""
    
    def __init__(self, storage_path: str = "training_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # S3を使う場合
        # self.s3 = boto3.client('s3')
        # self.bucket = "fx-training-data"
    
    def save_for_future_training(self, 
                                charts: Dict[str, Path], 
                                analysis: str, 
                                currency: str) -> None:
        """
        分析結果を学習用に保存（非同期でユーザーを待たせない）
        
        これは既存の処理に追加するだけで、
        ユーザーへの出力には影響しません
        """
        # 非同期で保存（メイン処理をブロックしない）
        asyncio.create_task(self._save_async(charts, analysis, currency))
    
    async def _save_async(self, charts: Dict, analysis: str, currency: str):
        """バックグラウンドでデータを保存"""
        try:
            # データ構造を作成
            training_data = {
                "id": f"{currency}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "currency_pair": currency,
                "input": {
                    "charts": {
                        timeframe: str(path) 
                        for timeframe, path in charts.items()
                    },
                    "market_conditions": self._get_market_conditions(currency)
                },
                "output": {
                    "analysis": analysis,
                    "predictions": self._extract_predictions(analysis)
                },
                "validation": {
                    "status": "pending",
                    "scheduled_for": (datetime.now() + timedelta(hours=24)).isoformat()
                }
            }
            
            # ローカルに保存
            filename = f"{training_data['id']}.json"
            filepath = self.storage_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"学習データを保存: {filename}")
            
            # S3に保存する場合
            # self._save_to_s3(training_data)
            
        except Exception as e:
            # エラーが起きてもメイン処理には影響しない
            logger.warning(f"学習データ保存エラー（継続）: {e}")
    
    def validate_yesterday_predictions(self):
        """
        24時間前の予測を検証（cronで実行）
        これも完全に独立した処理
        """
        yesterday = datetime.now() - timedelta(days=1)
        
        # 昨日のデータを読み込み
        for file in self.storage_path.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 24時間経過したデータのみ処理
                data_time = datetime.fromisoformat(data['timestamp'])
                if (datetime.now() - data_time).total_seconds() < 86400:
                    continue
                
                # 実際の市場結果を取得
                actual_result = self._get_actual_market_result(
                    data['currency_pair'],
                    data_time
                )
                
                # 精度を計算
                accuracy = self._calculate_accuracy(
                    predictions=data['output']['predictions'],
                    actual=actual_result
                )
                
                # 検証結果を更新
                data['validation'] = {
                    "status": "completed",
                    "accuracy": accuracy,
                    "actual_result": actual_result,
                    "validated_at": datetime.now().isoformat()
                }
                
                # 高品質データのみ訓練用に分類
                if accuracy > 0.8:
                    data['training_quality'] = "high"
                    self._move_to_training_set(file, data)
                    logger.info(f"高品質データを訓練セットに追加: {data['id']} (精度: {accuracy:.2%})")
                
            except Exception as e:
                logger.error(f"検証エラー: {file}, {e}")
    
    def _extract_predictions(self, analysis: str) -> Dict:
        """分析テキストから予測を抽出"""
        predictions = {
            "direction": None,
            "entry": None,
            "stop_loss": None,
            "take_profit": None
        }
        
        # テキストから価格を抽出（簡易版）
        import re
        
        # エントリー価格
        entry_match = re.search(r'エントリー[：:]\s*([\d.]+)', analysis)
        if entry_match:
            predictions["entry"] = float(entry_match.group(1))
        
        # 方向
        if "買い" in analysis or "ロング" in analysis or "上昇" in analysis:
            predictions["direction"] = "up"
        elif "売り" in analysis or "ショート" in analysis or "下降" in analysis:
            predictions["direction"] = "down"
        
        return predictions
    
    def _calculate_accuracy(self, predictions: Dict, actual: Dict) -> float:
        """予測精度を計算"""
        score = 0.0
        
        # 方向の精度（50%）
        if predictions.get("direction") == actual.get("direction"):
            score += 0.5
        
        # 価格レベルの精度（30%）
        if predictions.get("entry") and actual.get("price_hit"):
            price_diff = abs(predictions["entry"] - actual["price_hit"])
            if price_diff < 0.1:  # 0.1円以内
                score += 0.3
            elif price_diff < 0.3:  # 0.3円以内
                score += 0.15
        
        # リスクリワードの達成（20%）
        if actual.get("risk_reward_achieved"):
            score += 0.2
        
        return score
    
    def _move_to_training_set(self, file_path: Path, data: Dict):
        """高品質データを訓練用ディレクトリに移動"""
        training_dir = self.storage_path / "high_quality"
        training_dir.mkdir(exist_ok=True)
        
        # ファイルを移動
        new_path = training_dir / file_path.name
        file_path.rename(new_path)
        
        # メタデータを更新
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_training_stats(self) -> Dict:
        """収集した学習データの統計"""
        stats = {
            "total_predictions": 0,
            "validated": 0,
            "high_quality": 0,
            "pending": 0
        }
        
        for file in self.storage_path.rglob("*.json"):
            stats["total_predictions"] += 1
            
            with open(file, 'r') as f:
                data = json.load(f)
                
            if data['validation']['status'] == 'completed':
                stats["validated"] += 1
                if data.get('training_quality') == 'high':
                    stats["high_quality"] += 1
            else:
                stats["pending"] += 1
        
        return stats
    
    def _get_market_conditions(self, currency: str) -> Dict:
        """現在の市場状況を取得（簡易版）"""
        return {
            "volatility": "normal",
            "trend": "unknown",
            "session": "tokyo"
        }
    
    def _get_actual_market_result(self, currency: str, timestamp: datetime) -> Dict:
        """実際の市場結果を取得（実装が必要）"""
        # 実際にはyfinanceなどでデータ取得
        return {
            "direction": "up",
            "price_hit": 145.80,
            "risk_reward_achieved": True
        }


# 既存のコードへの統合例
def integrate_with_existing_code():
    """
    既存のmain.pyに追加するコード例
    """
    # 1. インポート追加
    from src.training_data_collector import TrainingDataCollector
    
    # 2. 初期化
    collector = TrainingDataCollector()
    
    # 3. 既存の分析関数に1行追加
    async def analyze_fx_charts():
        # ... 既存の処理 ...
        
        # チャート生成
        screenshots = generator.generate_charts()
        
        # Claude分析
        analysis = analyzer.analyze_charts(screenshots)
        
        # Notion保存
        notion.save(analysis)
        
        # ブログ投稿
        blog.post(analysis)
        
        # 【追加】学習データとして保存（非同期）
        collector.save_for_future_training(
            screenshots, analysis, "USD/JPY"
        )
        
        # ... 処理続行 ...