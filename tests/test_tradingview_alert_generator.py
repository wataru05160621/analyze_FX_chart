"""
TradingViewアラート設定生成のテストコード
半自動化機能のテスト駆動開発
"""
import unittest
from datetime import datetime
from pathlib import Path
import json
import tempfile
import os

# まだ実装していないクラスをインポート（後で実装）
from src.tradingview_alert_generator import (
    TradingViewAlertGenerator,
    PineScriptGenerator,
    AlertConfiguration,
    AlertType
)


class TestAlertConfiguration(unittest.TestCase):
    """アラート設定データクラスのテスト"""
    
    def test_create_buy_alert_config(self):
        """買いアラート設定の作成テスト"""
        config = AlertConfiguration(
            action='BUY',
            currency_pair='USD/JPY',
            entry_price=145.50,
            stop_loss=145.20,
            take_profit=146.00,
            confidence=0.85
        )
        
        self.assertEqual(config.action, 'BUY')
        self.assertEqual(config.currency_pair, 'USD/JPY')
        self.assertEqual(config.tv_symbol, 'USDJPY')
        self.assertEqual(config.entry_price, 145.50)
        self.assertEqual(config.stop_loss, 145.20)
        self.assertEqual(config.take_profit, 146.00)
        
    def test_create_sell_alert_config(self):
        """売りアラート設定の作成テスト"""
        config = AlertConfiguration(
            action='SELL',
            currency_pair='EUR/USD',
            entry_price=1.0850,
            stop_loss=1.0880,
            take_profit=1.0800,
            confidence=0.75
        )
        
        self.assertEqual(config.action, 'SELL')
        self.assertEqual(config.tv_symbol, 'EURUSD')
        
    def test_validate_config(self):
        """設定の検証テスト"""
        # 無効な設定（損切りが利確より良い）
        with self.assertRaises(ValueError):
            AlertConfiguration(
                action='BUY',
                currency_pair='USD/JPY',
                entry_price=145.50,
                stop_loss=146.00,  # エントリーより高い（無効）
                take_profit=145.00,  # エントリーより低い（無効）
                confidence=0.85
            )


class TestTradingViewAlertGenerator(unittest.TestCase):
    """TradingViewアラート生成クラスのテスト"""
    
    def setUp(self):
        self.generator = TradingViewAlertGenerator()
        self.buy_config = AlertConfiguration(
            action='BUY',
            currency_pair='USD/JPY',
            entry_price=145.50,
            stop_loss=145.20,
            take_profit=146.00,
            confidence=0.85
        )
        self.sell_config = AlertConfiguration(
            action='SELL',
            currency_pair='USD/JPY',
            entry_price=145.80,
            stop_loss=146.10,
            take_profit=145.50,
            confidence=0.80
        )
    
    def test_generate_entry_alert(self):
        """エントリーアラート生成のテスト"""
        alert = self.generator.generate_alert(
            self.buy_config,
            AlertType.ENTRY
        )
        
        self.assertEqual(alert['name'], 'USD/JPY 買いエントリー')
        self.assertEqual(alert['condition'], 'USDJPY >= 145.50')
        self.assertIn('BUY USDJPY', alert['message'])
        self.assertIn('Target: 146.00', alert['message'])
        self.assertIn('SL: 145.20', alert['message'])
        self.assertTrue(alert['webhook_enabled'])
        
    def test_generate_stop_loss_alert(self):
        """損切りアラート生成のテスト"""
        alert = self.generator.generate_alert(
            self.buy_config,
            AlertType.STOP_LOSS
        )
        
        self.assertEqual(alert['name'], 'USD/JPY 損切り')
        self.assertEqual(alert['condition'], 'USDJPY <= 145.20')
        self.assertIn('STOP LOSS', alert['message'])
        
    def test_generate_take_profit_alert(self):
        """利確アラート生成のテスト"""
        alert = self.generator.generate_alert(
            self.sell_config,
            AlertType.TAKE_PROFIT
        )
        
        self.assertEqual(alert['name'], 'USD/JPY 利確')
        self.assertEqual(alert['condition'], 'USDJPY <= 145.50')
        self.assertIn('TAKE PROFIT', alert['message'])
    
    def test_generate_all_alerts(self):
        """全アラート生成のテスト"""
        alerts = self.generator.generate_all_alerts(self.buy_config)
        
        self.assertEqual(len(alerts), 3)  # エントリー、損切り、利確
        
        # 各アラートタイプが含まれているか確認
        alert_names = [alert['name'] for alert in alerts]
        self.assertIn('USD/JPY 買いエントリー', alert_names)
        self.assertIn('USD/JPY 損切り', alert_names)
        self.assertIn('USD/JPY 利確', alert_names)
    
    def test_export_instructions(self):
        """設定手順のエクスポートテスト"""
        alerts = self.generator.generate_all_alerts(self.buy_config)
        instructions = self.generator.export_instructions(alerts, self.buy_config)
        
        self.assertIn('TradingViewアラート設定手順', instructions)
        self.assertIn('FX:USDJPY', instructions)
        self.assertIn('買いエントリー', instructions)
        self.assertIn('Webhook URL:', instructions)


class TestPineScriptGenerator(unittest.TestCase):
    """Pine Script生成のテスト"""
    
    def setUp(self):
        self.generator = PineScriptGenerator()
        self.config = AlertConfiguration(
            action='BUY',
            currency_pair='USD/JPY',
            entry_price=145.50,
            stop_loss=145.20,
            take_profit=146.00,
            confidence=0.85
        )
    
    def test_generate_pine_script(self):
        """Pine Script生成のテスト"""
        script = self.generator.generate_script(self.config)
        
        # 必要な要素が含まれているか確認
        self.assertIn('//@version=5', script)
        self.assertIn('indicator("FX Alert - USD/JPY"', script)
        self.assertIn('entry_price = 145.50', script)
        self.assertIn('stop_loss = 145.20', script)
        self.assertIn('take_profit = 146.00', script)
        self.assertIn('plot(entry_price', script)
        self.assertIn('alert(', script)
    
    def test_generate_alert_conditions(self):
        """アラート条件の生成テスト"""
        conditions = self.generator._generate_alert_conditions(self.config)
        
        self.assertIn('close >= entry_price', conditions)  # 買いエントリー
        self.assertIn('close <= stop_loss', conditions)    # 買い損切り
        self.assertIn('close >= take_profit', conditions)  # 買い利確
    
    def test_save_script_to_file(self):
        """スクリプトのファイル保存テスト"""
        script = self.generator.generate_script(self.config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pine', delete=False) as f:
            filepath = self.generator.save_script(script, f.name)
            
        self.assertTrue(Path(filepath).exists())
        
        # ファイル内容を確認
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertEqual(content, script)
        
        # クリーンアップ
        os.unlink(filepath)


class TestIntegrationWithPhase1(unittest.TestCase):
    """Phase 1との統合テスト"""
    
    def test_signal_to_alert_config(self):
        """Phase 1シグナルからアラート設定への変換テスト"""
        # Phase 1のシグナル形式
        phase1_signal = {
            'action': 'BUY',
            'entry_price': 145.50,
            'stop_loss': 145.20,
            'take_profit': 146.00,
            'confidence': 0.85
        }
        
        # アラート設定に変換
        config = AlertConfiguration.from_phase1_signal(
            phase1_signal,
            currency_pair='USD/JPY'
        )
        
        self.assertEqual(config.action, 'BUY')
        self.assertEqual(config.entry_price, 145.50)
        self.assertEqual(config.currency_pair, 'USD/JPY')
    
    def test_full_workflow(self):
        """完全なワークフローのテスト"""
        # Phase 1シグナル
        signal = {
            'action': 'SELL',
            'entry_price': 145.80,
            'stop_loss': 146.10,
            'take_profit': 145.50,
            'confidence': 0.80
        }
        
        # アラート設定生成
        config = AlertConfiguration.from_phase1_signal(signal, 'USD/JPY')
        
        # TradingViewアラート生成
        tv_generator = TradingViewAlertGenerator()
        alerts = tv_generator.generate_all_alerts(config)
        
        # Pine Script生成
        pine_generator = PineScriptGenerator()
        script = pine_generator.generate_script(config)
        
        # 検証
        self.assertEqual(len(alerts), 3)
        self.assertIn('//@version=5', script)
        
        # 設定手順の生成
        instructions = tv_generator.export_instructions(alerts, config)
        self.assertIn('売りエントリー', instructions)


class TestWebhookIntegration(unittest.TestCase):
    """Webhook統合のテスト"""
    
    def test_webhook_url_configuration(self):
        """Webhook URL設定のテスト"""
        generator = TradingViewAlertGenerator(
            webhook_url='https://example.com/webhook'
        )
        
        config = AlertConfiguration(
            action='BUY',
            currency_pair='USD/JPY',
            entry_price=145.50,
            stop_loss=145.20,
            take_profit=146.00,
            confidence=0.85
        )
        
        alert = generator.generate_alert(config, AlertType.ENTRY)
        
        self.assertTrue(alert['webhook_enabled'])
        self.assertEqual(
            generator.webhook_url,
            'https://example.com/webhook'
        )
    
    def test_webhook_message_format(self):
        """Webhookメッセージフォーマットのテスト"""
        generator = TradingViewAlertGenerator()
        
        message = generator._format_webhook_message(
            action='BUY',
            symbol='USDJPY',
            price='{{close}}',
            alert_type=AlertType.ENTRY
        )
        
        # JSON形式であることを確認
        self.assertIn('"action": "BUY"', message)
        self.assertIn('"symbol": "USDJPY"', message)
        self.assertIn('"price": {{close}}', message)
        self.assertIn('"alert_type": "ENTRY"', message)


if __name__ == '__main__':
    unittest.main()