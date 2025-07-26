"""
MT4とのブリッジモジュール
トレード結果を自動的に収集してデータベースに保存
"""
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from flask import Flask, request, jsonify
from pathlib import Path
import os

from phase1_data_collector import Phase1DataCollector, TradeRecord, MarketSnapshot

logger = logging.getLogger(__name__)

app = Flask(__name__)

# データコレクター初期化
collector = Phase1DataCollector()

@app.route('/mt4/trade_closed', methods=['POST'])
def trade_closed():
    """
    MT4からトレード終了通知を受信
    EAから送信されるデータ形式:
    {
        "ticket": 12345,
        "symbol": "USDJPY",
        "entry_price": 150.123,
        "entry_time": "2024-03-15 08:30:00",
        "exit_price": 150.323,
        "exit_time": "2024-03-15 09:05:00",
        "profit": 20.0,
        "pips": 20.0,
        "setup_type": "A",
        "comment": "Volman_A_TP"
    }
    """
    try:
        data = request.json
        logger.info(f"MT4トレード終了通知: {data}")
        
        # 追加情報を取得（チャート分析など）
        additional_info = analyze_trade_context(data)
        
        # TradeRecordを作成
        trade = TradeRecord(
            trade_id=f"MT4_{data['ticket']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            session=determine_session(),
            setup_type=data.get('setup_type', 'Unknown'),
            entry_price=float(data['entry_price']),
            entry_time=data['entry_time'],
            signal_quality=additional_info.get('signal_quality', 3),
            buildup_duration=additional_info.get('buildup_duration', 0),
            buildup_pattern=additional_info.get('buildup_pattern', 'Unknown'),
            ema_configuration=additional_info.get('ema_configuration', 'Unknown'),
            atr_at_entry=additional_info.get('atr', 0),
            spread_at_entry=additional_info.get('spread', 0),
            volatility_level=additional_info.get('volatility_level', 'Medium'),
            news_nearby=additional_info.get('news_nearby', False),
            exit_price=float(data['exit_price']),
            exit_time=data['exit_time'],
            exit_reason=determine_exit_reason(data['comment']),
            pips_result=float(data['pips']),
            profit_loss=float(data['profit']),
            max_favorable_excursion=additional_info.get('mfe', 0),
            max_adverse_excursion=additional_info.get('mae', 0),
            time_in_trade=calculate_trade_duration(data['entry_time'], data['exit_time']),
            entry_chart_path=additional_info.get('entry_chart', ''),
            exit_chart_path=additional_info.get('exit_chart', ''),
            ai_analysis_summary=additional_info.get('ai_summary', ''),
            confidence_score=additional_info.get('confidence', 0.5)
        )
        
        # データベースに保存
        collector.save_trade(trade)
        
        # 日次統計を更新
        today = datetime.now().strftime('%Y-%m-%d')
        collector.calculate_daily_stats(today)
        
        return jsonify({
            'status': 'success',
            'trade_id': trade.trade_id,
            'message': 'Trade recorded successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"トレード記録エラー: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/mt4/market_snapshot', methods=['POST'])
def market_snapshot():
    """
    MT4から定期的な市場スナップショットを受信
    """
    try:
        data = request.json
        
        snapshot = MarketSnapshot(
            timestamp=datetime.now().isoformat(),
            price=float(data['price']),
            ema_25=float(data['ema_25']),
            ema_75=float(data['ema_75']),
            ema_200=float(data['ema_200']),
            atr=float(data['atr']),
            spread=float(data['spread']),
            volume=data.get('volume'),
            session=determine_session(),
            major_news=data.get('news', [])
        )
        
        collector.save_market_snapshot(snapshot)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"スナップショット記録エラー: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/mt4/signal_generated', methods=['POST'])
def signal_generated():
    """
    MT4からシグナル生成通知を受信（エントリー前）
    """
    try:
        data = request.json
        logger.info(f"シグナル生成: {data}")
        
        # シグナル情報を一時保存（後でトレード結果と紐付け）
        signal_path = Path('phase1_data/signals')
        signal_path.mkdir(parents=True, exist_ok=True)
        
        signal_file = signal_path / f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(signal_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"シグナル記録エラー: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def determine_session() -> str:
    """現在のセッションを判定"""
    hour = datetime.now().hour
    
    if 7 <= hour < 15:  # 日本時間
        return "アジア"
    elif 15 <= hour < 21:
        return "ロンドン"
    else:
        return "NY"

def determine_exit_reason(comment: str) -> str:
    """コメントから終了理由を判定"""
    comment_upper = comment.upper()
    
    if 'TP' in comment_upper:
        return 'TP'
    elif 'SL' in comment_upper:
        return 'SL'
    else:
        return '手動'

def calculate_trade_duration(entry_time: str, exit_time: str) -> int:
    """トレード時間を計算（分）"""
    try:
        entry = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S')
        exit = datetime.strptime(exit_time, '%Y-%m-%d %H:%M:%S')
        duration = (exit - entry).total_seconds() / 60
        return int(duration)
    except:
        return 0

def analyze_trade_context(trade_data: Dict) -> Dict:
    """
    トレードのコンテキスト情報を分析
    実際の実装では、チャート画像生成やAI分析を行う
    """
    # TODO: 実装
    # 1. エントリー時のチャート画像を生成
    # 2. ビルドアップパターンを分析
    # 3. EMA配列を確認
    # 4. AI分析を実行
    
    return {
        'signal_quality': 4,
        'buildup_duration': 45,
        'buildup_pattern': '三角保ち合い',
        'ema_configuration': '上昇配列',
        'atr': 8.5,
        'spread': 1.2,
        'volatility_level': '中',
        'news_nearby': False,
        'mfe': 25.0,
        'mae': -5.0,
        'entry_chart': 'phase1_data/trade_charts/entry_example.png',
        'exit_chart': 'phase1_data/trade_charts/exit_example.png',
        'ai_summary': '良好なビルドアップからの明確なブレイク',
        'confidence': 0.85
    }

if __name__ == '__main__':
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/mt4_bridge.log'),
            logging.StreamHandler()
        ]
    )
    
    # サーバー起動
    app.run(host='0.0.0.0', port=5555, debug=False)