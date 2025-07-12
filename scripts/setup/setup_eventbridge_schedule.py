#!/usr/bin/env python3
"""
EventBridgeスケジュールを設定するスクリプト
"""
import boto3
import json
from datetime import datetime

def setup_eventbridge_schedules(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """EventBridgeスケジュールを設定"""
    events_client = boto3.client('events', region_name=region)
    lambda_client = boto3.client('lambda', region_name=region)
    
    # Lambda関数のARNを取得
    try:
        func_config = lambda_client.get_function_configuration(FunctionName=function_name)
        function_arn = func_config['FunctionArn']
        print(f"Lambda関数ARN: {function_arn}")
    except Exception as e:
        print(f"❌ Lambda関数が見つかりません: {e}")
        return False
    
    # スケジュール設定
    schedules = [
        {
            'name': 'fx-analysis-morning',
            'description': '朝8時の全プラットフォーム投稿',
            'schedule': 'cron(0 23 ? * * *)',  # UTC 23:00 = JST 8:00
            'enabled': True
        },
        {
            'name': 'fx-analysis-afternoon',
            'description': '午後3時のNotion投稿',
            'schedule': 'cron(0 6 ? * * *)',   # UTC 6:00 = JST 15:00
            'enabled': True
        },
        {
            'name': 'fx-analysis-evening',
            'description': '夜9時のNotion投稿',
            'schedule': 'cron(0 12 ? * * *)',  # UTC 12:00 = JST 21:00
            'enabled': True
        }
    ]
    
    for schedule in schedules:
        try:
            # ルールを作成/更新
            print(f"\n設定中: {schedule['name']}")
            
            events_client.put_rule(
                Name=schedule['name'],
                Description=schedule['description'],
                ScheduleExpression=schedule['schedule'],
                State='ENABLED' if schedule['enabled'] else 'DISABLED'
            )
            
            # ターゲットを追加
            events_client.put_targets(
                Rule=schedule['name'],
                Targets=[
                    {
                        'Id': '1',
                        'Arn': function_arn,
                        'Input': json.dumps({
                            'schedule': schedule['name'],
                            'time': 'morning' if 'morning' in schedule['name'] else 'other'
                        })
                    }
                ]
            )
            
            # Lambda実行権限を追加
            try:
                lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=f'allow-eventbridge-{schedule["name"]}',
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=f'arn:aws:events:{region}:{func_config["FunctionArn"].split(":")[4]}:rule/{schedule["name"]}'
                )
            except lambda_client.exceptions.ResourceConflictException:
                # 既に権限が存在する場合は無視
                pass
            
            print(f"✅ {schedule['name']} 設定完了")
            print(f"   スケジュール: {schedule['schedule']}")
            print(f"   説明: {schedule['description']}")
            
        except Exception as e:
            print(f"❌ {schedule['name']} 設定エラー: {e}")
    
    # 設定確認
    print("\n=== 設定されたスケジュール ===")
    rules = events_client.list_rules()
    for rule in rules['Rules']:
        if 'fx-analysis' in rule['Name']:
            print(f"- {rule['Name']}: {rule.get('ScheduleExpression', 'N/A')} ({rule['State']})")
    
    return True

def test_lambda_invocation(function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数のテスト実行"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    print(f"\n=== Lambda関数 '{function_name}' のテスト実行 ===")
    
    try:
        # テストイベント
        test_event = {
            'test': True,
            'schedule': 'manual-test',
            'time': 'test'
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # レスポンスを解析
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"ステータスコード: {status_code}")
        
        if status_code == 200:
            print("✅ テスト実行成功")
            print(f"レスポンス: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        else:
            print("❌ テスト実行失敗")
            print(f"エラー: {payload}")
            
        # ログストリーム名を表示
        if 'LogResult' in response:
            print(f"\nログを確認: aws logs tail /aws/lambda/{function_name} --follow")
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        print("\n権限エラーの場合は、AWS Consoleから直接テストを実行してください")

def main():
    print("=== EventBridgeスケジュール設定 ===\n")
    
    # スケジュール設定
    if setup_eventbridge_schedules():
        print("\n✅ スケジュール設定完了")
        
        # テスト実行
        print("\nテスト実行しますか？ (y/n): ", end='')
        if input().lower() == 'y':
            test_lambda_invocation()
    
    print("\n完了！")
    print("\n次回の自動実行:")
    print("- 翌朝 8:00 JST: 全プラットフォーム投稿")
    print("- 15:00 JST: Notion投稿")
    print("- 21:00 JST: Notion投稿")

if __name__ == "__main__":
    main()