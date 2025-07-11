#!/bin/bash
# cronジョブ設定スクリプト

echo "=== FX分析システム cron設定 ==="
echo

# プロジェクトディレクトリ
PROJECT_DIR="/Users/shinzato/programing/claude_code/analyze_FX_chart"
PYTHON_PATH="/usr/bin/python3"

# ログディレクトリ作成
mkdir -p "$PROJECT_DIR/logs/cron"

# cron実行用スクリプト作成
cat > "$PROJECT_DIR/run_scheduled_analysis.sh" << 'EOF'
#!/bin/bash
# スケジュール実行用スクリプト

# 環境変数設定
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export LANG=ja_JP.UTF-8

# プロジェクトディレクトリに移動
cd /Users/shinzato/programing/claude_code/analyze_FX_chart

# ログファイル
LOG_FILE="logs/cron/analysis_$(date +%Y%m%d).log"

# 実行タイプを判定
HOUR=$(date +%H)
if [ "$HOUR" = "08" ]; then
    TYPE="full"
    SESSION="アジアセッション"
elif [ "$HOUR" = "15" ]; then
    TYPE="notion"
    SESSION="ロンドンセッション"
elif [ "$HOUR" = "21" ]; then
    TYPE="notion"
    SESSION="NYセッション"
else
    echo "不正な実行時間: $HOUR時" >> "$LOG_FILE"
    exit 1
fi

echo "=== 分析実行開始: $(date) ===" >> "$LOG_FILE"
echo "タイプ: $TYPE, セッション: $SESSION" >> "$LOG_FILE"

# Python実行
if [ "$TYPE" = "full" ]; then
    # 8時: フル投稿
    python3 execute_complete_posting.py >> "$LOG_FILE" 2>&1
else
    # 15時/21時: Notionのみ
    python3 execute_notion_only.py --session "$SESSION" >> "$LOG_FILE" 2>&1
fi

echo "=== 分析実行完了: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
EOF

# 実行権限付与
chmod +x "$PROJECT_DIR/run_scheduled_analysis.sh"

# Notionのみ投稿用スクリプト作成
cat > "$PROJECT_DIR/execute_notion_only.py" << 'EOF'
#!/usr/bin/env python3
"""
Notionのみ投稿スクリプト（15時、21時用）
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

# セッション名取得
session_name = "定期分析"
if len(sys.argv) > 2 and sys.argv[1] == "--session":
    session_name = sys.argv[2]

print(f"=== Notion投稿実行 ({session_name}) ===")
print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 環境変数読み込み
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            if '#' in line:
                line = line.split('#')[0].strip()
            key, value = line.strip().split('=', 1)
            if value and value not in ['your_value_here', 'your_api_key_here']:
                os.environ[key] = value

if os.path.exists('.env.phase1'):
    with open('.env.phase1', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# モジュールインポート
from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer
from src.notion_writer import NotionWriter
from src.notion_analyzer import NotionAnalyzer

try:
    # 1. チャート生成
    print("\n1. チャート生成...")
    generator = ChartGenerator('USDJPY=X')
    output_dir = Path('screenshots') / f"{session_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    screenshots = generator.generate_multiple_charts(
        timeframes=['5min', '1hour'],
        output_dir=output_dir,
        candle_count=288
    )
    print(f"✅ チャート生成完了")
    
    # 2. Claude分析
    print("\n2. Claude分析...")
    analyzer = ClaudeAnalyzer()
    analysis = analyzer.analyze_charts(screenshots)
    print(f"✅ 分析完了: {len(analysis)}文字")
    
    # 3. Notion投稿（詳細版）
    print("\n3. Notion投稿...")
    notion_analyzer = NotionAnalyzer()
    detailed_analysis = notion_analyzer.create_detailed_analysis(analysis)
    
    writer = NotionWriter()
    page_id = writer.create_analysis_page(
        f"USD/JPY分析 {session_name} {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        detailed_analysis,
        screenshots,
        "USD/JPY"
    )
    print(f"✅ Notion投稿成功: {page_id}")
    
    # 4. Slack通知
    print("\n4. Slack通知...")
    import requests
    webhook = os.environ.get('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/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')
    message = {
        "text": f"*FX分析完了 ({session_name})*\n"
               f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
               f"Notion投稿完了"
    }
    resp = requests.post(webhook, json=message)
    if resp.status_code == 200:
        print("✅ Slack通知送信")
    
    print("\n✅ 完了!")
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()
    
    # エラー通知
    try:
        import requests
        webhook = os.environ.get('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/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')
        message = {
            "text": f"*⚠️ FX分析エラー ({session_name})*\n"
                   f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                   f"エラー: {str(e)}"
        }
        requests.post(webhook, json=message)
    except:
        pass
    
    sys.exit(1)
EOF

chmod +x "$PROJECT_DIR/execute_notion_only.py"

# crontab設定内容
echo "以下の内容をcrontabに追加してください:"
echo "（crontab -e で編集）"
echo
echo "# FX分析システム スケジュール実行"
echo "# 平日8時: ブログ、X、Notion投稿"
echo "0 8 * * 1-5 cd $PROJECT_DIR && ./run_scheduled_analysis.sh"
echo
echo "# 平日15時: Notion投稿のみ"
echo "0 15 * * 1-5 cd $PROJECT_DIR && ./run_scheduled_analysis.sh"
echo
echo "# 平日21時: Notion投稿のみ"
echo "0 21 * * 1-5 cd $PROJECT_DIR && ./run_scheduled_analysis.sh"
echo
echo "# または、Pythonスケジューラーを常時実行"
echo "# @reboot cd $PROJECT_DIR && nohup python3 scheduled_execution.py > logs/scheduler.log 2>&1 &"
echo

# 手動テスト方法
echo "=== テスト実行方法 ==="
echo "# フル投稿テスト（8時相当）"
echo "python3 scheduled_execution.py --test full"
echo
echo "# Notionのみテスト（15時/21時相当）"
echo "python3 scheduled_execution.py --test notion"
echo
echo "# 通常のスケジューラー起動"
echo "python3 scheduled_execution.py"