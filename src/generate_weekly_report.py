#!/usr/bin/env python
"""週次パフォーマンスレポート生成"""
from phase1_performance_automation import Phase1PerformanceAutomation
import pandas as pd
from datetime import datetime, timedelta

def main():
    print(f"=== 週次レポート生成: {datetime.now()} ===")
    
    performance = Phase1PerformanceAutomation()
    
    # 過去7日間のシグナルを集計
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    weekly_signals = [
        s for s in performance.performance_data["signals"]
        if start_date.isoformat() <= s["timestamp"] <= end_date.isoformat()
    ]
    
    # 週次統計
    weekly_stats = {
        "期間": f"{start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')}",
        "シグナル数": len(weekly_signals),
        "実行数": len([s for s in weekly_signals if s["status"] == "completed"]),
        "勝率": performance.performance_data["statistics"].get("win_rate", 0),
        "週間期待値": performance.performance_data["statistics"].get("expected_value_percentage", 0),
        "累計損益": sum(s.get("pnl", 0) for s in weekly_signals if s.get("pnl"))
    }
    
    # レポート保存
    filename = f"performance/weekly/report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, 'w') as f:
        json.dump(weekly_stats, f, indent=2, ensure_ascii=False)
    
    print(f"週次レポート生成完了: {filename}")

if __name__ == "__main__":
    main()
