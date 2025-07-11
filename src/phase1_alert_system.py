"""
Phase 1: TradingViewアラートシステムの実装
分析結果から売買シグナルを生成し、各種通知を送信
"""
import re
import json
import smtplib
import requests
from datetime import datetime
from typing import Dict, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from decimal import Decimal
import uuid
import os


class SignalGenerator:
    """分析テキストから構造化された売買シグナルを生成"""
    
    def generate_trading_signal(self, analysis_text: str) -> Dict:
        """
        分析テキストから売買シグナルを生成
        
        Args:
            analysis_text: 分析結果のテキスト
            
        Returns:
            売買シグナルの辞書
        """
        signal = {
            "action": "NONE",
            "entry_price": 0,
            "stop_loss": 0,
            "take_profit": 0,
            "confidence": 0
        }
        
        # アクションの判定
        if any(word in analysis_text for word in ["強い上昇", "ブレイクアウト", "買いエントリー", "上昇トレンド"]):
            signal["action"] = "BUY"
            signal["confidence"] = 0.8
        elif any(word in analysis_text for word in ["下落トレンド", "売りシグナル", "売りエントリー", "下降"]):
            signal["action"] = "SELL"
            signal["confidence"] = 0.8
        elif any(word in analysis_text for word in ["様子見", "不明瞭", "レンジ"]):
            return signal  # NONEのまま返す
        
        # 価格レベルの抽出
        if signal["action"] != "NONE":
            signal["entry_price"] = self._extract_entry_price(analysis_text)
            signal["stop_loss"] = self._extract_stop_loss(analysis_text)
            signal["take_profit"] = self._extract_take_profit(analysis_text)
        
        return signal
    
    def _extract_entry_price(self, text: str) -> float:
        """エントリー価格を抽出"""
        patterns = [
            r"エントリー[:：]\s*(\d+\.?\d*)",
            r"(\d+\.?\d*)で.*ブレイクアウト",
            r"(\d+\.?\d*)で.*[買売]りシグナル",
            r"(\d+\.?\d*)でエントリー",
            r"(\d+\.?\d*)を.*エントリー",
            r"entry at (\d+\.?\d*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return 0
    
    def _extract_stop_loss(self, text: str) -> float:
        """損切り価格を抽出"""
        patterns = [
            r"(\d+\.?\d*)を損切り",
            r"損切り[:：]\s*(\d+\.?\d*)",
            r"ストップロス[:：]\s*(\d+\.?\d*)",
            r"SL[:：]\s*(\d+\.?\d*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return 0
    
    def _extract_take_profit(self, text: str) -> float:
        """利確価格を抽出"""
        patterns = [
            r"(\d+\.?\d*)を目標",
            r"目標[:：]\s*(\d+\.?\d*)",
            r"利確[:：]\s*(\d+\.?\d*)",
            r"TP[:：]\s*(\d+\.?\d*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return 0


class TradingViewAlertSystem:
    """売買アラートを各種プラットフォームに送信"""
    
    def __init__(self):
        self.webhook_url = os.environ.get('SLACK_WEBHOOK_URL', '')
        self.tradingview_webhook = os.environ.get('TRADINGVIEW_WEBHOOK_URL', '')
        self.email_config = {
            'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
            'sender_email': os.environ.get('SENDER_EMAIL', ''),
            'sender_password': os.environ.get('SENDER_PASSWORD', ''),
            'recipient_email': os.environ.get('RECIPIENT_EMAIL', '')
        }
    
    def send_trade_alert(self, analysis_result: Dict) -> Dict:
        """
        分析結果から売買アラートを生成して送信
        
        Args:
            analysis_result: 分析結果とシグナル情報
            
        Returns:
            送信したアラート情報
        """
        alert = {
            "symbol": "USD/JPY",
            "action": analysis_result['signal']['action'],
            "entry": analysis_result['signal']['entry_price'],
            "stop_loss": analysis_result['signal']['stop_loss'],
            "take_profit": analysis_result['signal']['take_profit'],
            "confidence": analysis_result['signal']['confidence'],
            "analysis": analysis_result.get('summary', '')
        }
        
        # 各プラットフォームに送信
        if self.webhook_url:
            self._send_slack_notification(alert)
        
        if self.tradingview_webhook:
            self._send_to_tradingview(alert)
        
        if self.email_config['sender_email']:
            self._send_email_alert(alert)
        
        return alert
    
    def _send_slack_notification(self, alert: Dict):
        """Slack通知を送信"""
        message = self._format_slack_message(alert)
        
        payload = {
            "text": message
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Slack通知エラー: {e}")
    
    def _format_slack_message(self, alert: Dict) -> str:
        """Slack用のメッセージフォーマット"""
        emoji = "📈" if alert['action'] == 'BUY' else "📉" if alert['action'] == 'SELL' else "⏸️"
        
        message = f"""
{emoji} *FX売買シグナル*
通貨ペア: {alert['symbol']}
アクション: {alert['action']}
エントリー: {alert['entry']}
損切り: {alert['stop_loss']}
利確: {alert['take_profit']}
信頼度: {alert['confidence']:.1%}

分析: {alert['analysis']}
"""
        return message
    
    def _send_to_tradingview(self, alert: Dict):
        """TradingViewにWebhook送信"""
        # TradingView用のフォーマットに変換
        tv_data = {
            "ticker": alert['symbol'].replace('/', ''),
            "action": alert['action'].lower(),
            "price": alert['entry'],
            "stop_loss": alert['stop_loss'],
            "take_profit": alert['take_profit']
        }
        
        try:
            response = requests.post(
                self.tradingview_webhook,
                data=json.dumps(tv_data),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"TradingView通知エラー: {e}")
    
    def _send_email_alert(self, alert: Dict):
        """メール通知を送信"""
        if not all([self.email_config['sender_email'], 
                   self.email_config['recipient_email'],
                   self.email_config['sender_password']]):
            return
        
        # メールメッセージ作成
        msg = MIMEMultipart()
        msg['From'] = self.email_config['sender_email']
        msg['To'] = self.email_config['recipient_email']
        msg['Subject'] = f"FX売買シグナル: {alert['symbol']} {alert['action']}"
        
        body = f"""
FX売買シグナルが発生しました。

通貨ペア: {alert['symbol']}
アクション: {alert['action']}
エントリー価格: {alert['entry']}
損切り価格: {alert['stop_loss']}
利確価格: {alert['take_profit']}
信頼度: {alert['confidence']:.1%}

分析内容:
{alert['analysis']}

※このメールは自動送信されています。
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)
        except Exception as e:
            print(f"メール送信エラー: {e}")


class DynamoDBClient:
    """DynamoDB操作用クライアント（モック可能）"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
    
    def get_table(self, table_name: str):
        """テーブルを取得"""
        return self.dynamodb.Table(table_name)


class PerformanceTracker:
    """シグナルのパフォーマンスを記録・追跡"""
    
    def __init__(self):
        self.db_client = DynamoDBClient()
        self.table_name = os.environ.get('PERFORMANCE_TABLE', 'fx-trading-signals')
        self._records = {}  # テスト用のインメモリストレージ
    
    def record_signal(self, signal: Dict) -> str:
        """
        シグナルを記録
        
        Args:
            signal: 売買シグナル
            
        Returns:
            記録ID
        """
        record_id = str(uuid.uuid4())
        
        record = {
            'id': record_id,
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'executed': False,
            'result': None
        }
        
        # 本番環境ではDynamoDBに保存
        if hasattr(self.db_client, 'get_table'):
            try:
                table = self.db_client.get_table(self.table_name)
                # DynamoDB用にDecimal変換
                record_for_db = self._convert_to_decimal(record)
                table.put_item(Item=record_for_db)
            except:
                # テスト環境ではインメモリに保存
                self._records[record_id] = record
        else:
            self._records[record_id] = record
        
        return record_id
    
    def update_signal_result(self, signal_id: str, result: Dict):
        """シグナルの実行結果を更新"""
        if signal_id in self._records:
            self._records[signal_id]['executed'] = True
            self._records[signal_id]['result'] = result
        else:
            # DynamoDBから更新
            try:
                table = self.db_client.get_table(self.table_name)
                table.update_item(
                    Key={'id': signal_id},
                    UpdateExpression='SET executed = :e, result = :r',
                    ExpressionAttributeValues={
                        ':e': True,
                        ':r': self._convert_to_decimal(result)
                    }
                )
            except:
                pass
    
    def get_signal_record(self, signal_id: str) -> Optional[Dict]:
        """シグナル記録を取得"""
        if signal_id in self._records:
            return self._records[signal_id]
        
        try:
            table = self.db_client.get_table(self.table_name)
            response = table.get_item(Key={'id': signal_id})
            return response.get('Item')
        except:
            return None
    
    def calculate_statistics(self, signals: List[Dict]) -> Dict:
        """統計情報を計算（期待値重視）"""
        total_signals = len(signals)
        executed_signals = sum(1 for s in signals if s.get('executed', False))
        
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0
        wins = []
        losses = []
        
        for signal in signals:
            if signal.get('executed') and signal.get('result'):
                pnl = signal['result'].get('pnl', 0)
                total_pnl += pnl
                
                if pnl > 0:
                    winning_trades += 1
                    wins.append(pnl)
                elif pnl < 0:
                    losing_trades += 1
                    losses.append(abs(pnl))
        
        win_rate = winning_trades / executed_signals if executed_signals > 0 else 0
        average_win = sum(wins) / len(wins) if wins else 0
        average_loss = sum(losses) / len(losses) if losses else 0
        
        # 期待値の計算
        expected_value = (win_rate * average_win) - ((1 - win_rate) * average_loss)
        risk_reward_ratio = average_win / average_loss if average_loss > 0 else 0
        
        return {
            'total_signals': total_signals,
            'executed_signals': executed_signals,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'average_win': average_win,
            'average_loss': average_loss,
            'expected_value': expected_value,
            'risk_reward_ratio': risk_reward_ratio
        }
    
    def _convert_to_decimal(self, obj):
        """DynamoDB用にfloatをDecimalに変換"""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_decimal(v) for v in obj]
        return obj