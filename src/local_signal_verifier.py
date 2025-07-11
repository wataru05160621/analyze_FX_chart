#!/usr/bin/env python3
"""
ローカル環境での24時間後シグナル検証
Lambda使用不可の場合の代替実装
"""
import json
import os
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import Dict
import schedule
import requests

# .env.phase1ファイルから環境変数を読み込み
def load_env_file():
    """環境変数ファイルを読み込み"""
    env_file = '.env.phase1'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# 環境変数を読み込み
load_env_file()

class LocalSignalVerifier:
    """ローカル環境でのシグナル検証"""
    
    def __init__(self):
        self.performance_file = "phase1_performance.json"
        self.verification_queue_file = "verification_queue.json"
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        
        # 検証キューを読み込み
        self.load_verification_queue()
        
        # スケジューラーを開始
        self.start_scheduler()
    
    def load_verification_queue(self):
        """検証キューを読み込み"""
        if os.path.exists(self.verification_queue_file):
            with open(self.verification_queue_file, 'r') as f:
                self.queue = json.load(f)
        else:
            self.queue = []
    
    def save_verification_queue(self):
        """検証キューを保存"""
        with open(self.verification_queue_file, 'w') as f:
            json.dump(self.queue, f, indent=2)
    
    def schedule_verification(self, signal_id: str, verify_at: str):
        """検証をスケジュール"""
        self.queue.append({
            "signal_id": signal_id,
            "verify_at": verify_at,
            "status": "pending"
        })
        self.save_verification_queue()
        print(f"✅ ローカル検証をスケジュール: {signal_id} at {verify_at}")
    
    def check_and_verify(self):
        """期限が来たシグナルを検証"""
        now = datetime.now()
        
        for item in self.queue:
            if item['status'] == 'pending':
                verify_time = datetime.fromisoformat(item['verify_at'])
                
                if now >= verify_time:
                    print(f"🔍 検証実行: {item['signal_id']}")
                    self.verify_signal(item['signal_id'])
                    item['status'] = 'completed'
                    self.save_verification_queue()
    
    def verify_signal(self, signal_id: str):
        """シグナルを検証"""
        # パフォーマンスデータを読み込み
        with open(self.performance_file, 'r') as f:
            data = json.load(f)
        
        # シグナルを検索
        signal = None
        for s in data['signals']:
            if s['id'] == signal_id:
                signal = s
                break
        
        if not signal:
            print(f"❌ シグナルが見つかりません: {signal_id}")
            return
        
        # 現在価格を取得（デモ価格）
        current_price = self.get_current_price(signal.get('currency_pair', 'USDJPY'))
        
        # 結果を判定
        result = self.calculate_result(signal, current_price)
        
        # シグナルを更新
        signal['status'] = 'completed' if result['result'] != 'OPEN' else 'active'
        signal['result'] = result['result']
        signal['actual_exit'] = result['exit_price']
        signal['pnl'] = result['pnl']
        signal['pnl_percentage'] = result['pnl_percentage']
        signal['verified_at'] = datetime.now().isoformat()
        
        # 統計を再計算
        self.recalculate_statistics(data)
        
        # 保存
        with open(self.performance_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Slack通知
        if self.slack_webhook:
            self.send_slack_notification(signal, result)
        
        print(f"✅ 検証完了: {signal_id} - {result['result']}")
    
    def get_current_price(self, currency_pair: str) -> float:
        """現在価格を取得（デモ実装）"""
        # Alpha Vantage APIキーがある場合は実際の価格を取得
        api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        
        if api_key and api_key != 'demo':
            try:
                from_currency = currency_pair[:3]
                to_currency = currency_pair[3:6]
                
                url = f"https://www.alphavantage.co/query"
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'apikey': api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if 'Realtime Currency Exchange Rate' in data:
                    rate = float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
                    print(f"📊 実際の価格を取得: {currency_pair} = {rate}")
                    return rate
            except Exception as e:
                print(f"⚠️ 価格取得エラー: {e}")
        
        # デモ価格
        demo_prices = {
            'USDJPY': 145.75,
            'USD/JPY': 145.75,
            'EURUSD': 1.0850,
            'EUR/USD': 1.0850
        }
        return demo_prices.get(currency_pair, 145.50)
    
    def calculate_result(self, signal: Dict, current_price: float) -> Dict:
        """結果を計算"""
        entry_price = float(signal['entry_price'])
        stop_loss = float(signal['stop_loss'])
        take_profit = float(signal['take_profit'])
        action = signal['action']
        
        if action == 'BUY':
            if current_price >= take_profit:
                result = 'TP_HIT'
                exit_price = take_profit
            elif current_price <= stop_loss:
                result = 'SL_HIT'
                exit_price = stop_loss
            else:
                result = 'OPEN'
                exit_price = current_price
            pnl = exit_price - entry_price
        else:  # SELL
            if current_price <= take_profit:
                result = 'TP_HIT'
                exit_price = take_profit
            elif current_price >= stop_loss:
                result = 'SL_HIT'
                exit_price = stop_loss
            else:
                result = 'OPEN'
                exit_price = current_price
            pnl = entry_price - exit_price
        
        pnl_percentage = (pnl / entry_price) * 100
        
        return {
            'result': result,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage
        }
    
    def recalculate_statistics(self, data: Dict):
        """統計を再計算"""
        completed = [s for s in data['signals'] if s.get('status') == 'completed']
        
        if not completed:
            return
        
        wins = [s for s in completed if s.get('pnl', 0) > 0]
        losses = [s for s in completed if s.get('pnl', 0) <= 0]
        
        win_rate = len(wins) / len(completed)
        avg_win = sum(s.get('pnl', 0) for s in wins) / len(wins) if wins else 0
        avg_loss = sum(abs(s.get('pnl', 0)) for s in losses) / len(losses) if losses else 0
        
        expected_value = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        data['statistics'] = {
            'total_trades': len(completed),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'expected_value': expected_value,
            'expected_value_percentage': expected_value / 145.0 * 100,
            'risk_reward_ratio': avg_win / avg_loss if avg_loss > 0 else 0,
            'last_updated': datetime.now().isoformat()
        }
    
    def send_slack_notification(self, signal: Dict, result: Dict):
        """Slack通知"""
        emoji = "✅" if result['pnl'] > 0 else "❌" if result['pnl'] < 0 else "⏳"
        
        message = f"""
{emoji} Phase 1 シグナル検証結果（ローカル）

シグナルID: {signal['id']}
通貨ペア: {signal.get('currency_pair', 'USD/JPY')}
アクション: {signal['action']}
結果: {result['result']}

エントリー: {signal['entry_price']}
エグジット: {result['exit_price']}
損益: {result['pnl']:.1f} pips ({result['pnl_percentage']:.2f}%)

検証時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        try:
            requests.post(self.slack_webhook, json={"text": message})
        except Exception as e:
            print(f"Slack通知エラー: {e}")
    
    def start_scheduler(self):
        """スケジューラーを開始"""
        # 1分ごとに検証チェック
        schedule.every(1).minutes.do(self.check_and_verify)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        # バックグラウンドスレッドで実行
        scheduler_thread = Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("✅ ローカル検証スケジューラーを開始しました")
    
    def run_once(self):
        """即座に1回だけ検証を実行"""
        self.check_and_verify()


# Alpha Vantage API取得用のヘルパー関数
def setup_alpha_vantage():
    """Alpha Vantage APIキーを設定"""
    print("\n=== Alpha Vantage API設定 ===")
    print("無料APIキーを取得: https://www.alphavantage.co/support/#api-key")
    print("\nデモ用の仮想価格を使用する場合は 'demo' と入力してください")
    
    api_key = input("Alpha Vantage APIキー (またはdemo): ").strip()
    
    if api_key and api_key != 'demo':
        # .env.phase1に追記
        with open('.env.phase1', 'a') as f:
            f.write(f"\n# 価格取得API\nALPHA_VANTAGE_API_KEY={api_key}\n")
        
        os.environ['ALPHA_VANTAGE_API_KEY'] = api_key
        print("✅ Alpha Vantage APIキーを設定しました")
        
        # テスト
        verifier = LocalSignalVerifier()
        price = verifier.get_current_price('USDJPY')
        print(f"テスト価格取得: USD/JPY = {price}")
    else:
        print("ℹ️ デモ価格を使用します")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'setup-api':
        setup_alpha_vantage()
    else:
        # 通常の検証実行
        verifier = LocalSignalVerifier()
        
        if len(sys.argv) > 1:
            # 手動でシグナルを検証
            signal_id = sys.argv[1]
            verifier.verify_signal(signal_id)
        else:
            # スケジューラーを実行
            print("ローカル検証システムを実行中...")
            print("Ctrl+Cで終了")
            
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                print("\n終了します")