"""
シグナル検証をEventBridge経由でスケジュール
"""
import boto3
import json
from datetime import datetime, timedelta

eventbridge = boto3.client('events', region_name='ap-northeast-1')

def schedule_verification(signal_id, currency_pair='USDJPY', hours_later=24):
    """
    Lambda検証をスケジュール
    
    Args:
        signal_id: シグナルID
        currency_pair: 通貨ペア
        hours_later: 何時間後に検証するか（デフォルト24時間）
    """
    # スケジュール時刻を計算
    scheduled_time = datetime.now() + timedelta(hours=hours_later)
    
    # EventBridgeルールを作成
    rule_name = f"verify-signal-{signal_id}"
    
    # スケジュール式（cron形式）
    # 例: 2025-01-10 15:30 → cron(30 15 10 1 ? 2025)
    cron_expression = f"cron({scheduled_time.minute} {scheduled_time.hour} {scheduled_time.day} {scheduled_time.month} ? {scheduled_time.year})"
    
    try:
        # ルール作成
        eventbridge.put_rule(
            Name=rule_name,
            ScheduleExpression=cron_expression,
            State='ENABLED',
            Description=f'Verify signal {signal_id} at {scheduled_time}'
        )
        
        # ターゲット（Lambda関数）を追加
        lambda_arn = f"arn:aws:lambda:ap-northeast-1:455931011903:function:phase1-signal-verification-prod-verifySignal"
        
        eventbridge.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': '1',
                    'Arn': lambda_arn,
                    'Input': json.dumps({
                        'source': 'phase1.signals',
                        'detail-type': 'Signal Verification Scheduled',
                        'detail': {
                            'signal_id': signal_id,
                            'currency_pair': currency_pair,
                            'scheduled_for': scheduled_time.isoformat()
                        }
                    })
                }
            ]
        )
        
        print(f"✅ 検証スケジュール設定完了: {signal_id} at {scheduled_time}")
        
        # 一度だけ実行したら削除するように設定
        # （24時間後に自動削除）
        eventbridge.put_rule(
            Name=f"cleanup-{rule_name}",
            ScheduleExpression=f"cron({scheduled_time.minute} {scheduled_time.hour} {scheduled_time.day + 1} {scheduled_time.month} ? {scheduled_time.year})",
            State='ENABLED',
            Description=f'Cleanup rule for {rule_name}'
        )
        
        return {
            'rule_name': rule_name,
            'scheduled_time': scheduled_time.isoformat(),
            'status': 'scheduled'
        }
        
    except Exception as e:
        print(f"❌ スケジュール設定エラー: {e}")
        return {
            'error': str(e),
            'status': 'failed'
        }


# Phase 1パフォーマンス記録時に自動的に呼び出される
def integrate_with_phase1():
    """Phase 1と統合"""
    from phase1_performance_automation import Phase1PerformanceAutomation
    
    # 既存のrecord_signal関数を拡張
    original_record_signal = Phase1PerformanceAutomation.record_signal
    
    def record_signal_with_scheduling(self, signal, analysis_result):
        # 元の関数を実行
        signal_id = original_record_signal(self, signal, analysis_result)
        
        # EventBridge検証をスケジュール
        currency_pair = analysis_result.get('currency_pair', 'USDJPY')
        schedule_verification(signal_id, currency_pair)
        
        return signal_id
    
    # 関数を置き換え
    Phase1PerformanceAutomation.record_signal = record_signal_with_scheduling

if __name__ == "__main__":
    # テスト実行
    import sys
    if len(sys.argv) > 1:
        test_signal_id = sys.argv[1]
        result = schedule_verification(test_signal_id, hours_later=0.1)  # 6分後にテスト
        print(json.dumps(result, indent=2))
