#!/usr/bin/env python
"""Production test script - runs FX analysis with AWS resources."""

import os
import sys
import json
import boto3
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_environment():
    """Setup environment variables from AWS Secrets Manager."""
    print("🔧 Setting up environment from AWS Secrets Manager...")
    
    secrets_client = boto3.client('secretsmanager', region_name='ap-northeast-1')
    
    # Get secrets
    secrets_to_fetch = [
        'NOTION_API_KEY',
        'NOTION_DB_ID',
        'SLACK_WEBHOOK_URL',
        'S3_BUCKET',
        'TWELVEDATA_API_KEY'
    ]
    
    for secret_name in secrets_to_fetch:
        try:
            response = secrets_client.get_secret_value(SecretId=secret_name)
            secret_value = response['SecretString']
            os.environ[secret_name] = secret_value
            print(f"  ✓ {secret_name}: {'*' * 10}")
        except Exception as e:
            print(f"  ❌ Failed to get {secret_name}: {e}")
    
    # Set other environment variables
    os.environ['APP_NAME'] = 'analyze-fx'
    os.environ['TZ'] = 'Asia/Tokyo'
    os.environ['PAIR'] = 'USDJPY'
    os.environ['SYMBOL'] = 'USD/JPY'
    os.environ['TIMEFRAMES'] = '5m,1h'
    os.environ['S3_PREFIX'] = 'charts'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['DATA_SOURCE'] = 'twelvedata'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'
    
    print("  ✓ Environment configured")

def run_analysis():
    """Run the FX analysis."""
    print("\n🚀 Starting FX Analysis (Production Test)...")
    print("=" * 60)
    
    try:
        from src.runner.main import FXAnalysisRunner
        
        runner = FXAnalysisRunner()
        results = runner.run()
        
        return results
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_outputs(results):
    """Verify the outputs were created."""
    print("\n📊 Verifying Outputs...")
    print("=" * 60)
    
    if not results:
        print("❌ No results to verify")
        return False
    
    success = True
    
    # Check analysis results
    if 'analysis' in results:
        analysis = results['analysis']
        print(f"✓ Analysis completed:")
        print(f"  - Run ID: {analysis.get('run_id')}")
        print(f"  - Setup: {analysis.get('final_setup')}")
        print(f"  - Confidence: {analysis.get('confidence')}")
        print(f"  - EV: {analysis.get('ev_R')}")
    else:
        print("❌ No analysis results")
        success = False
    
    # Check S3 uploads
    if 's3' in results and results['s3']:
        print(f"✓ S3 uploads:")
        if 'charts' in results['s3']:
            for tf, info in results['s3']['charts'].items():
                print(f"  - {tf} chart: {info.get('key', 'N/A')}")
        if 'json' in results['s3']:
            print(f"  - JSON: {results['s3']['json'].get('key', 'N/A')}")
    else:
        print("⚠️  S3 uploads failed or skipped")
    
    # Check Notion
    if 'notion_page_id' in results:
        print(f"✓ Notion page created: {results['notion_page_id']}")
    else:
        print("⚠️  Notion page creation failed or skipped")
    
    # Check Slack
    if 'slack_sent' in results and results['slack_sent']:
        print(f"✓ Slack notification sent")
    else:
        print("⚠️  Slack notification failed or skipped")
    
    # Check errors
    if results.get('errors'):
        print(f"\n⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    return success

def check_cloudwatch_logs():
    """Check CloudWatch logs for the run."""
    print("\n📊 Checking CloudWatch Logs...")
    
    logs_client = boto3.client('logs', region_name='ap-northeast-1')
    log_group = '/ecs/analyze-fx'
    
    try:
        # Get latest log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if response['logStreams']:
            stream = response['logStreams'][0]
            print(f"  Latest log stream: {stream['logStreamName']}")
            
            if 'lastEventTimestamp' in stream:
                last_event = datetime.fromtimestamp(stream['lastEventTimestamp'] / 1000)
                print(f"  Last event: {last_event.isoformat()}")
        else:
            print("  No log streams found")
            
    except Exception as e:
        print(f"  ⚠️  Could not check logs: {e}")

def main():
    """Main function."""
    print("🧪 FX Analysis System - Production Test")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Run analysis
    results = run_analysis()
    
    # Verify outputs
    if results:
        verify_outputs(results)
        
        # Save results for inspection
        with open('test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to test_results.json")
        
        # Check logs
        check_cloudwatch_logs()
        
        if results['status'] == 'completed':
            print("\n✅ Production test completed successfully!")
            return 0
        elif results['status'] == 'completed_with_errors':
            print("\n⚠️  Production test completed with some errors")
            return 1
        else:
            print("\n❌ Production test failed")
            return 2
    else:
        print("\n❌ Production test failed - no results")
        return 3

if __name__ == "__main__":
    sys.exit(main())