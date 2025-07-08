"""
Phase 1: TradingViewアラートシステムのテストコード
テスト駆動開発(TDD)に基づいて先にテストを作成
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
from typing import Dict

# まだ実装していないクラスをインポート（後で実装）
from src.phase1_alert_system import (
    TradingViewAlertSystem,
    SignalGenerator,
    PerformanceTracker
)


class TestSignalGenerator(unittest.TestCase):
    """シグナル生成ロジックのテスト"""
    
    def setUp(self):
        self.generator = SignalGenerator()
    
    def test_generate_buy_signal_from_analysis(self):
        """買いシグナルが正しく生成されることをテスト"""
        analysis_text = """
        USD/JPYは強い上昇トレンドを形成しています。
        145.50でのブレイクアウトが確認され、
        146.00を目標に、145.20を損切りラインとして
        買いエントリーを推奨します。
        """
        
        signal = self.generator.generate_trading_signal(analysis_text)
        
        self.assertEqual(signal['action'], 'BUY')
        self.assertEqual(signal['entry_price'], 145.50)
        self.assertEqual(signal['stop_loss'], 145.20)
        self.assertEqual(signal['take_profit'], 146.00)
        self.assertGreaterEqual(signal['confidence'], 0.7)
    
    def test_generate_sell_signal_from_analysis(self):
        """売りシグナルが正しく生成されることをテスト"""
        analysis_text = """
        下落トレンドが継続しており、145.80での売りシグナルが
        点灯しています。145.50を目標に、146.10を損切りラインと
        して売りエントリーを検討してください。
        """
        
        signal = self.generator.generate_trading_signal(analysis_text)
        
        self.assertEqual(signal['action'], 'SELL')
        self.assertEqual(signal['entry_price'], 145.80)
        self.assertEqual(signal['stop_loss'], 146.10)
        self.assertEqual(signal['take_profit'], 145.50)
        self.assertGreaterEqual(signal['confidence'], 0.7)
    
    def test_no_signal_when_unclear(self):
        """明確なシグナルがない場合はNONEを返すことをテスト"""
        analysis_text = """
        現在のUSD/JPYは方向感が不明瞭で、
        レンジ相場となっています。
        明確なトレンドが形成されるまで様子見を推奨します。
        """
        
        signal = self.generator.generate_trading_signal(analysis_text)
        
        self.assertEqual(signal['action'], 'NONE')
        self.assertEqual(signal['confidence'], 0)
    
    def test_extract_price_levels(self):
        """価格レベルの抽出が正しく行われることをテスト"""
        test_cases = [
            ("エントリー: 145.50", 145.50),
            ("エントリー：145.50", 145.50),
            ("145.50でエントリー", 145.50),
            ("entry at 145.50", 145.50),
        ]
        
        for text, expected in test_cases:
            result = self.generator._extract_entry_price(text)
            self.assertEqual(result, expected)


class TestTradingViewAlertSystem(unittest.TestCase):
    """アラートシステムのテスト"""
    
    def setUp(self):
        self.alert_system = TradingViewAlertSystem()
        self.sample_analysis = {
            'signal': {
                'action': 'BUY',
                'entry_price': 145.50,
                'stop_loss': 145.20,
                'take_profit': 146.00,
                'confidence': 0.85
            },
            'summary': 'Strong uptrend detected'
        }
    
    @patch('requests.post')
    def test_send_slack_notification(self, mock_post):
        """Slack通知が正しく送信されることをテスト"""
        mock_post.return_value.status_code = 200
        
        alert = self.alert_system.send_trade_alert(self.sample_analysis)
        
        # Slack APIが呼ばれたことを確認
        mock_post.assert_called()
        call_args = mock_post.call_args
        
        # 送信されたメッセージの内容を確認
        sent_data = json.loads(call_args[1]['data'])
        self.assertIn('FX売買シグナル', sent_data['text'])
        self.assertIn('USD/JPY', sent_data['text'])
        self.assertIn('BUY', sent_data['text'])
        self.assertIn('145.50', sent_data['text'])
    
    @patch('smtplib.SMTP')
    def test_send_email_alert(self, mock_smtp):
        """メール通知が正しく送信されることをテスト"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        self.alert_system._send_email_alert({
            'symbol': 'USD/JPY',
            'action': 'BUY',
            'entry': 145.50,
            'stop_loss': 145.20,
            'take_profit': 146.00,
            'confidence': 0.85,
            'analysis': 'Test analysis'
        })
        
        # メールが送信されたことを確認
        mock_server.send_message.assert_called_once()
    
    def test_format_alert_message(self):
        """アラートメッセージのフォーマットをテスト"""
        alert = {
            'symbol': 'USD/JPY',
            'action': 'BUY',
            'entry': 145.50,
            'stop_loss': 145.20,
            'take_profit': 146.00,
            'confidence': 0.85,
            'analysis': 'Strong uptrend'
        }
        
        message = self.alert_system._format_slack_message(alert)
        
        # 必要な情報が含まれているか確認
        self.assertIn('USD/JPY', message)
        self.assertIn('BUY', message)
        self.assertIn('145.50', message)
        self.assertIn('145.20', message)
        self.assertIn('146.00', message)
        self.assertIn('85.0%', message)
    
    @patch('requests.post')
    def test_tradingview_webhook(self, mock_post):
        """TradingViewへのWebhook送信をテスト"""
        mock_post.return_value.status_code = 200
        
        alert = {
            'symbol': 'USD/JPY',
            'action': 'BUY',
            'entry': 145.50,
            'stop_loss': 145.20,
            'take_profit': 146.00
        }
        
        self.alert_system._send_to_tradingview(alert)
        
        # TradingView用のフォーマットで送信されたか確認
        mock_post.assert_called()
        sent_data = json.loads(mock_post.call_args[1]['data'])
        self.assertEqual(sent_data['ticker'], 'USDJPY')
        self.assertEqual(sent_data['action'], 'buy')


class TestPerformanceTracker(unittest.TestCase):
    """パフォーマンス記録のテスト"""
    
    def setUp(self):
        self.tracker = PerformanceTracker()
        self.sample_signal = {
            'action': 'BUY',
            'entry_price': 145.50,
            'stop_loss': 145.20,
            'take_profit': 146.00,
            'confidence': 0.85
        }
    
    @patch('src.phase1_alert_system.DynamoDBClient')
    def test_record_signal(self, mock_dynamodb):
        """シグナルが正しく記録されることをテスト"""
        mock_table = MagicMock()
        mock_dynamodb.return_value.get_table.return_value = mock_table
        
        record_id = self.tracker.record_signal(self.sample_signal)
        
        # DynamoDBに保存されたことを確認
        mock_table.put_item.assert_called_once()
        saved_item = mock_table.put_item.call_args[0][0]
        
        self.assertEqual(saved_item['signal'], self.sample_signal)
        self.assertEqual(saved_item['executed'], False)
        self.assertIsNone(saved_item['result'])
        self.assertIsNotNone(saved_item['timestamp'])
        self.assertEqual(saved_item['id'], record_id)
    
    def test_update_signal_result(self):
        """シグナルの結果更新をテスト"""
        signal_id = "test-signal-123"
        result = {
            'executed': True,
            'actual_entry': 145.48,
            'actual_exit': 145.95,
            'pnl': 470,
            'pnl_percentage': 0.32
        }
        
        self.tracker.update_signal_result(signal_id, result)
        
        # 結果が更新されたことを確認
        updated_record = self.tracker.get_signal_record(signal_id)
        self.assertTrue(updated_record['executed'])
        self.assertEqual(updated_record['result'], result)
    
    def test_calculate_statistics(self):
        """統計情報の計算をテスト"""
        # テスト用のシグナル履歴を作成
        test_signals = [
            {'executed': True, 'result': {'pnl': 500}},
            {'executed': True, 'result': {'pnl': -200}},
            {'executed': True, 'result': {'pnl': 300}},
            {'executed': False, 'result': None},
            {'executed': True, 'result': {'pnl': -100}},
        ]
        
        stats = self.tracker.calculate_statistics(test_signals)
        
        self.assertEqual(stats['total_signals'], 5)
        self.assertEqual(stats['executed_signals'], 4)
        self.assertEqual(stats['winning_trades'], 2)
        self.assertEqual(stats['losing_trades'], 2)
        self.assertEqual(stats['win_rate'], 0.5)
        self.assertEqual(stats['total_pnl'], 500)
        self.assertEqual(stats['average_win'], 400)
        self.assertEqual(stats['average_loss'], -150)


class TestIntegration(unittest.TestCase):
    """統合テスト"""
    
    @patch('requests.post')
    @patch('src.phase1_alert_system.DynamoDBClient')
    def test_full_alert_flow(self, mock_dynamodb, mock_requests):
        """分析から通知までの完全なフローをテスト"""
        # セットアップ
        mock_requests.return_value.status_code = 200
        mock_table = MagicMock()
        mock_dynamodb.return_value.get_table.return_value = mock_table
        
        # システム初期化
        alert_system = TradingViewAlertSystem()
        generator = SignalGenerator()
        tracker = PerformanceTracker()
        
        # 分析テキスト
        analysis_text = """
        USD/JPYは145.50で強いブレイクアウトを確認。
        146.00を目標に、145.20を損切りとして買いエントリー推奨。
        上昇トレンドが継続する可能性が高い。
        """
        
        # 1. シグナル生成
        signal = generator.generate_trading_signal(analysis_text)
        self.assertEqual(signal['action'], 'BUY')
        
        # 2. アラート送信
        analysis_result = {
            'signal': signal,
            'summary': 'Breakout detected'
        }
        alert = alert_system.send_trade_alert(analysis_result)
        
        # 3. パフォーマンス記録
        record_id = tracker.record_signal(signal)
        
        # 検証
        self.assertIsNotNone(record_id)
        mock_requests.assert_called()  # 通知が送信された
        mock_table.put_item.assert_called()  # 記録が保存された


if __name__ == '__main__':
    unittest.main()