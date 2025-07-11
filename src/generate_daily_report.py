#!/usr/bin/env python
"""日次パフォーマンスレポート生成"""
from phase1_performance_automation import Phase1PerformanceAutomation
import json
from datetime import datetime

def main():
    print(f"=== 日次レポート生成: {datetime.now()} ===")
    
    performance = Phase1PerformanceAutomation()
    report = performance.generate_performance_report()
    
    # レポート保存
    filename = f"performance/daily/report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # CSV出力
    csv_file = performance.export_to_csv(
        f"performance/daily/signals_{datetime.now().strftime('%Y%m%d')}.csv"
    )
    
    print(f"レポート生成完了: {filename}")
    print(f"CSV出力: {csv_file}")
    
    # Slack通知
    # TODO: Slack通知実装

if __name__ == "__main__":
    main()
