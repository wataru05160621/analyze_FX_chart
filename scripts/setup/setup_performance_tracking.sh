#!/bin/bash

# Phase 1パフォーマンス追跡の自動セットアップ

echo "=== Phase 1 パフォーマンス追跡セットアップ ==="

# 1. 必要なディレクトリ作成
echo "1. ディレクトリ作成..."
mkdir -p performance/{daily,weekly,monthly}
mkdir -p logs/performance

# 2. 環境変数追加
echo "2. 環境変数設定..."
if ! grep -q "ENABLE_PHASE1" .env.phase1; then
    cat >> .env.phase1 << EOF

# パフォーマンス追跡設定
ENABLE_PHASE1=true
PERFORMANCE_S3_BUCKET=fx-analysis-performance
PERFORMANCE_TABLE=phase1-performance
VERIFY_AFTER_HOURS=24
EOF
fi

# 3. cronジョブ設定
echo "3. cronジョブ設定..."
cat > performance_cron.txt << EOF
# Phase 1 パフォーマンス追跡
# 毎日21:00に日次レポート生成
0 21 * * * cd $(pwd) && python src/generate_daily_report.py >> logs/performance/daily.log 2>&1

# 毎週月曜日に週次レポート
0 9 * * 1 cd $(pwd) && python src/generate_weekly_report.py >> logs/performance/weekly.log 2>&1

# 毎月1日に月次レポート
0 9 1 * * cd $(pwd) && python src/generate_monthly_report.py >> logs/performance/monthly.log 2>&1
EOF

echo "cronジョブを追加しますか？ (y/n)"
read -r response
if [[ "$response" == "y" ]]; then
    crontab -l > current_cron.txt 2>/dev/null || true
    cat performance_cron.txt >> current_cron.txt
    crontab current_cron.txt
    rm current_cron.txt performance_cron.txt
    echo "cronジョブを追加しました"
fi

# 4. レポート生成スクリプト作成
echo "4. レポート生成スクリプト作成..."

# 日次レポート
cat > src/generate_daily_report.py << 'EOF'
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
EOF

# 週次レポート
cat > src/generate_weekly_report.py << 'EOF'
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
EOF

chmod +x src/generate_daily_report.py
chmod +x src/generate_weekly_report.py

# 5. 初期パフォーマンスファイル作成
echo "5. 初期ファイル作成..."
if [ ! -f phase1_performance.json ]; then
    cat > phase1_performance.json << EOF
{
  "signals": [],
  "statistics": {},
  "last_updated": null
}
EOF
fi

# 6. AWS Lambda関数のテンプレート
echo "6. Lambda関数テンプレート作成..."
cat > lambda_verify_signal.py << 'EOF'
import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """24時間後のシグナル検証"""
    
    # S3からパフォーマンスデータを読み込み
    s3 = boto3.client('s3')
    bucket = os.environ['PERFORMANCE_S3_BUCKET']
    key = 'phase1_performance.json'
    
    response = s3.get_object(Bucket=bucket, Key=key)
    performance_data = json.loads(response['Body'].read())
    
    # シグナル検証ロジック
    signal_id = event['signal_id']
    
    # TODO: 実際の価格取得と検証ロジック
    
    # 結果をS3に保存
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(performance_data),
        ContentType='application/json'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Signal verified')
    }
EOF

echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ："
echo "1. main_multi_currency.pyに統合コードを追加"
echo "2. AWS Lambdaに検証関数をデプロイ（オプション）"
echo "3. python src/generate_daily_report.py でテスト実行"
echo ""
echo "環境変数 ENABLE_PHASE1=true でパフォーマンス追跡が有効化されます"