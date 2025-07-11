"""
Phase 1 パフォーマンス自動記録システム
シグナル生成から結果検証まで自動化
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import boto3
from decimal import Decimal
import pandas as pd
import schedule
import time
import requests

class Phase1PerformanceAutomation:
    """Phase 1のパフォーマンスを自動記録・追跡"""
    
    def __init__(self):
        self.performance_file = "phase1_performance.json"
        self.s3_bucket = os.environ.get('S3_BUCKET', 'fx-analysis-performance')
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        
        # パフォーマンスデータの初期化
        self.load_or_create_performance_data()
    
    def load_or_create_performance_data(self):
        """既存のパフォーマンスデータを読み込むか新規作成"""
        if os.path.exists(self.performance_file):
            with open(self.performance_file, 'r') as f:
                self.performance_data = json.load(f)
        else:
            self.performance_data = {
                "signals": [],
                "statistics": {},
                "last_updated": None
            }
    
    def record_signal(self, signal: Dict, analysis_result: Dict) -> str:
        """シグナルを自動記録"""
        signal_id = f"sig_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        record = {
            "id": signal_id,
            "timestamp": datetime.now().isoformat(),
            "currency_pair": "USD/JPY",  # TODO: 動的に取得
            "signal": signal,
            "analysis": analysis_result.get('summary', ''),
            "entry_price": signal['entry_price'],
            "stop_loss": signal['stop_loss'],
            "take_profit": signal['take_profit'],
            "action": signal['action'],
            "confidence": signal['confidence'],
            "status": "pending",  # pending, executed, completed
            "result": None,
            "actual_entry": None,
            "actual_exit": None,
            "pnl": None,
            "pnl_percentage": None
        }
        
        self.performance_data["signals"].append(record)
        self.save_performance_data()
        
        # 24時間後の自動検証をスケジュール
        self.schedule_verification(signal_id)
        
        return signal_id
    
    def update_signal_execution(self, signal_id: str, execution_data: Dict):
        """シグナル実行時の情報を更新"""
        for signal in self.performance_data["signals"]:
            if signal["id"] == signal_id:
                signal["status"] = "executed"
                signal["actual_entry"] = execution_data.get("entry_price")
                signal["execution_time"] = datetime.now().isoformat()
                break
        
        self.save_performance_data()
    
    def verify_signal_result(self, signal_id: str):
        """24時間後にシグナルの結果を自動検証"""
        signal = self.get_signal_by_id(signal_id)
        if not signal:
            return
        
        # 現在の価格を取得（実際の実装では価格APIを使用）
        current_price = self.get_current_price(signal["currency_pair"])
        
        # 結果を判定
        if signal["action"] == "BUY":
            if current_price >= signal["take_profit"]:
                result = "TP_HIT"
                exit_price = signal["take_profit"]
            elif current_price <= signal["stop_loss"]:
                result = "SL_HIT"
                exit_price = signal["stop_loss"]
            else:
                result = "OPEN"
                exit_price = current_price
        else:  # SELL
            if current_price <= signal["take_profit"]:
                result = "TP_HIT"
                exit_price = signal["take_profit"]
            elif current_price >= signal["stop_loss"]:
                result = "SL_HIT"
                exit_price = signal["stop_loss"]
            else:
                result = "OPEN"
                exit_price = current_price
        
        # PnLを計算
        if signal["action"] == "BUY":
            pnl = exit_price - signal["entry_price"]
        else:
            pnl = signal["entry_price"] - exit_price
        
        pnl_percentage = (pnl / signal["entry_price"]) * 100
        
        # 記録を更新
        signal["status"] = "completed" if result != "OPEN" else "active"
        signal["result"] = result
        signal["actual_exit"] = exit_price
        signal["pnl"] = pnl
        signal["pnl_percentage"] = pnl_percentage
        signal["verified_at"] = datetime.now().isoformat()
        
        self.save_performance_data()
        self.calculate_statistics()
        
        # 結果をSlack通知
        self.notify_signal_result(signal)
    
    def calculate_statistics(self):
        """統計情報を自動計算（Volman固定20/10期待値ベース）"""
        completed_signals = [s for s in self.performance_data["signals"] 
                           if s["status"] == "completed"]
        
        if not completed_signals:
            return
        
        # 基本統計
        total_trades = len(completed_signals)
        winning_trades = len([s for s in completed_signals if s["pnl"] > 0])
        losing_trades = len([s for s in completed_signals if s["pnl"] <= 0])
        
        # 勝率
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Volmanメソッドの固定値
        volman_profit = 20  # pips
        volman_loss = 10    # pips
        
        # 実際の平均損益（検証用）
        wins = [s["pnl"] for s in completed_signals if s["pnl"] > 0]
        losses = [abs(s["pnl"]) for s in completed_signals if s["pnl"] <= 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        # Volman期待値計算
        volman_expected_value = (win_rate * volman_profit) - ((1 - win_rate) * volman_loss)
        
        # 実際の期待値（比較用）
        actual_expected_value = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # リスクリワード比（Volmanは固定2:1）
        volman_risk_reward_ratio = 2.0
        actual_risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # プロフィットファクター
        gross_profit = sum(wins)
        gross_loss = sum(losses)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # 最大ドローダウン
        cumulative_pnl = []
        running_pnl = 0
        for signal in completed_signals:
            running_pnl += signal["pnl"]
            cumulative_pnl.append(running_pnl)
        
        if cumulative_pnl:
            peak = cumulative_pnl[0]
            max_drawdown = 0
            for pnl in cumulative_pnl:
                if pnl > peak:
                    peak = pnl
                drawdown = peak - pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        else:
            max_drawdown = 0
        
        # 統計を保存（Volmanメソッド対応）
        self.performance_data["statistics"] = {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "required_win_rate": 0.334,  # Volman最低基準33.4%
            "win_rate_vs_required": win_rate - 0.334,
            "volman_expected_value_pips": volman_expected_value,
            "volman_expected_value_percentage": volman_expected_value / 145.0 * 100,  # USD/JPY基準
            "actual_average_win": avg_win,
            "actual_average_loss": avg_loss,
            "actual_expected_value": actual_expected_value,
            "actual_expected_value_percentage": actual_expected_value / 145.0 * 100,
            "volman_risk_reward_ratio": volman_risk_reward_ratio,
            "actual_risk_reward_ratio": actual_risk_reward_ratio,
            "profit_factor": profit_factor,
            "total_pnl": sum([s["pnl"] for s in completed_signals]),
            "max_drawdown": max_drawdown,
            "max_consecutive_losses": self._calculate_max_consecutive_losses(completed_signals),
            "last_updated": datetime.now().isoformat()
        }
        
        self.save_performance_data()
    
    def generate_performance_report(self) -> Dict:
        """パフォーマンスレポートを自動生成"""
        stats = self.performance_data.get("statistics", {})
        
        report = {
            "title": "Phase 1 パフォーマンスレポート",
            "period": self._get_report_period(),
            "summary": {
                "総取引数": stats.get("total_trades", 0),
                "勝ちトレード": stats.get("winning_trades", 0),
                "負けトレード": stats.get("losing_trades", 0),
                "勝率": f"{stats.get('win_rate', 0):.1%} (必要: 33.4%)",
                "Volman期待値": f"{stats.get('volman_expected_value_pips', 0):.1f} pips/取引",
                "実際の期待値": f"{stats.get('actual_expected_value_pips', 0):.1f} pips/取引",
                "リスクリワード比": f"目標2:1 (実際: {stats.get('actual_risk_reward_ratio', 0):.2f})",
                "プロフィットファクター": f"{stats.get('profit_factor', 0):.2f}",
                "累計損益": f"{stats.get('total_pnl', 0):.1f} pips",
                "最大ドローダウン": f"{stats.get('max_drawdown', 0):.1f} pips"
            },
            "recent_signals": self._get_recent_signals(5),
            "recommendations": self._generate_recommendations(stats)
        }
        
        return report
    
    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """Volmanメソッドに基づく推奨事項を生成"""
        recommendations = []
        
        # 勝率チェック（Volman基準）
        win_rate = stats.get("win_rate", 0)
        if win_rate < 0.334:
            recommendations.append(f"⚠️ 勝率{win_rate:.1%}が最低基準33.4%を下回っています。セットアップの質を改善してください。")
        elif win_rate >= 0.45:
            recommendations.append(f"✅ 勝率{win_rate:.1%}は優秀です。Phase 2への移行を検討できます。")
        
        # Volman期待値チェック
        volman_ev = stats.get("volman_expected_value_pips", 0)
        if volman_ev < 0:
            recommendations.append(f"⚠️ Volman期待値が{volman_ev:.1f}pipsとマイナスです。勝率向上が必要です。")
        elif volman_ev >= 3.5:
            recommendations.append(f"✅ Volman期待値{volman_ev:.1f}pips/取引は非常に良好です。")
        
        # 実際の損益との乖離チェック
        actual_rr = stats.get("actual_risk_reward_ratio", 0)
        if actual_rr < 1.8:  # 2:1の90%
            recommendations.append("⚠️ 実際のリスクリワード比がVolman基準(2:1)を下回っています。早めの利確を避けてください。")
        
        # 連続損失チェック
        max_consecutive = stats.get("max_consecutive_losses", 0)
        if max_consecutive >= 5:
            recommendations.append(f"⚠️ 最大連続損失が{max_consecutive}回です。スキップルールの見直しを推奨。")
        
        # ドローダウンチェック（Volman基準）
        if stats.get("max_drawdown", 0) > 100:  # 10連敗相当
            recommendations.append("⚠️ 最大ドローダウンが100pipsを超えています。ポジションサイズの見直しを推奨。")
        
        return recommendations
    
    def save_performance_data(self):
        """パフォーマンスデータを保存"""
        with open(self.performance_file, 'w') as f:
            json.dump(self.performance_data, f, indent=2, ensure_ascii=False)
        
        # S3にもバックアップ（オプション）
        if hasattr(self, 's3_client'):
            self._backup_to_s3()
    
    def notify_signal_result(self, signal: Dict):
        """シグナル結果をSlack通知"""
        if not self.slack_webhook:
            return
        
        emoji = "✅" if signal["pnl"] > 0 else "❌"
        message = f"""
{emoji} Phase 1 シグナル結果

通貨ペア: {signal["currency_pair"]}
アクション: {signal["action"]}
結果: {signal["result"]}
損益: {signal["pnl"]:.1f} pips ({signal["pnl_percentage"]:.2f}%)

エントリー: {signal["entry_price"]}
エグジット: {signal["actual_exit"]}
"""
        
        requests.post(self.slack_webhook, json={"text": message})
    
    def schedule_verification(self, signal_id: str):
        """24時間後の検証をスケジュール"""
        # ローカル検証を使用
        try:
            from .local_signal_verifier import LocalSignalVerifier
            verifier = LocalSignalVerifier()
            
            verify_hours = float(os.environ.get('VERIFY_AFTER_HOURS', '24'))
            verification_time = datetime.now() + timedelta(hours=verify_hours)
            
            verifier.schedule_verification(signal_id, verification_time.isoformat())
            print(f"✅ ローカル検証スケジュール設定: {signal_id} at {verification_time}")
            
        except Exception as e:
            print(f"⚠️ 検証スケジュール設定エラー: {e}")
            verification_time = datetime.now() + timedelta(hours=24)
            print(f"検証スケジュール（手動）: {signal_id} at {verification_time}")
    
    def get_signal_by_id(self, signal_id: str) -> Optional[Dict]:
        """IDでシグナルを取得"""
        for signal in self.performance_data["signals"]:
            if signal["id"] == signal_id:
                return signal
        return None
    
    def get_current_price(self, currency_pair: str) -> float:
        """現在価格を取得（実装では価格APIを使用）"""
        # 仮の実装
        return 145.75
    
    def _calculate_max_consecutive_losses(self, completed_signals: List[Dict]) -> int:
        """最大連続損失数を計算"""
        if not completed_signals:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for signal in completed_signals:
            if signal.get("pnl", 0) <= 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _get_report_period(self) -> str:
        """レポート期間を取得"""
        if not self.performance_data["signals"]:
            return "データなし"
        
        first_signal = self.performance_data["signals"][0]
        last_signal = self.performance_data["signals"][-1]
        
        return f"{first_signal['timestamp'][:10]} 〜 {last_signal['timestamp'][:10]}"
    
    def _get_recent_signals(self, count: int) -> List[Dict]:
        """最近のシグナルを取得"""
        return self.performance_data["signals"][-count:]
    
    def export_to_csv(self, filename: Optional[str] = None):
        """パフォーマンスデータをCSVエクスポート"""
        if not filename:
            filename = f"phase1_performance_{datetime.now().strftime('%Y%m%d')}.csv"
        
        df = pd.DataFrame(self.performance_data["signals"])
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        return filename


# 使用例
if __name__ == "__main__":
    automation = Phase1PerformanceAutomation()
    
    # 新しいシグナルを記録
    sample_signal = {
        "action": "BUY",
        "entry_price": 145.50,
        "stop_loss": 145.20,
        "take_profit": 146.00,
        "confidence": 0.85
    }
    
    signal_id = automation.record_signal(sample_signal, {"summary": "テスト分析"})
    print(f"シグナル記録完了: {signal_id}")
    
    # パフォーマンスレポート生成
    report = automation.generate_performance_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))