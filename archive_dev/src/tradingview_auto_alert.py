"""
TradingViewアラート自動設定
Phase 1の分析結果に基づいてアラートを自動作成
"""
import asyncio
from playwright.async_api import async_playwright
import json
from typing import Dict, List
import os
from datetime import datetime
from .phase1_alert_system import SignalGenerator
from .logger import setup_logger

logger = setup_logger(__name__)


class TradingViewAutoAlert:
    """TradingViewのアラートを自動設定"""
    
    def __init__(self):
        self.email = os.environ.get('TRADINGVIEW_EMAIL', '')
        self.password = os.environ.get('TRADINGVIEW_PASSWORD', '')
        self.webhook_url = os.environ.get('TRADINGVIEW_WEBHOOK_URL', '')
        
    async def create_alert_from_signal(self, signal: Dict, currency_pair: str = "USDJPY"):
        """Phase 1のシグナルからTradingViewアラートを作成"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # デバッグ用に表示
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # TradingViewにログイン
                await self._login(page)
                
                # チャートを開く
                await page.goto(f'https://www.tradingview.com/chart/?symbol=FX:{currency_pair}')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                
                # アラートダイアログを開く
                await page.click('button[aria-label="Alert"]')
                await asyncio.sleep(1)
                
                # アラート条件を設定
                await self._set_alert_condition(page, signal)
                
                # Webhook URLを設定
                if self.webhook_url:
                    await self._set_webhook(page)
                
                # アラートメッセージを設定
                alert_message = self._create_alert_message(signal, currency_pair)
                await page.fill('textarea[placeholder="Message"]', alert_message)
                
                # アラートを作成
                await page.click('button:has-text("Create")')
                await asyncio.sleep(2)
                
                logger.info(f"TradingViewアラート作成完了: {currency_pair} - {signal['action']}")
                
            except Exception as e:
                logger.error(f"アラート作成エラー: {e}")
                
            finally:
                await browser.close()
    
    async def _login(self, page):
        """TradingViewにログイン"""
        await page.goto('https://www.tradingview.com/')
        
        # サインインボタンをクリック
        await page.click('button:has-text("Sign in")')
        await asyncio.sleep(1)
        
        # メールでログイン
        await page.click('span:has-text("Email")')
        await page.fill('input[name="username"]', self.email)
        await page.fill('input[name="password"]', self.password)
        await page.click('button[type="submit"]')
        
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
    
    async def _set_alert_condition(self, page, signal: Dict):
        """アラート条件を設定"""
        
        if signal['action'] == 'BUY':
            # 買いシグナルの条件
            # 価格が指定レベルを上回ったらアラート
            await page.select_option('select[name="condition"]', 'crossing_up')
            await page.fill('input[name="price"]', str(signal['entry_price']))
            
        elif signal['action'] == 'SELL':
            # 売りシグナルの条件
            await page.select_option('select[name="condition"]', 'crossing_down')
            await page.fill('input[name="price"]', str(signal['entry_price']))
    
    async def _set_webhook(self, page):
        """Webhook設定"""
        # Webhookチェックボックスを有効化
        await page.check('input[type="checkbox"][name="webhook"]')
        await page.fill('input[name="webhook-url"]', self.webhook_url)
    
    def _create_alert_message(self, signal: Dict, currency_pair: str) -> str:
        """アラートメッセージを作成"""
        return f"""
{signal['action']} {currency_pair}
Entry: {signal['entry_price']}
SL: {signal['stop_loss']}
TP: {signal['take_profit']}
Confidence: {signal['confidence']:.1%}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""


class PineScriptGenerator:
    """Pine Scriptでアラート条件を自動生成"""
    
    def generate_alert_script(self, signal: Dict) -> str:
        """シグナルからPine Scriptを生成"""
        
        if signal['action'] == 'BUY':
            condition = f"close > {signal['entry_price']}"
            alert_message = f"BUY Signal - Entry: {signal['entry_price']}"
        else:
            condition = f"close < {signal['entry_price']}"
            alert_message = f"SELL Signal - Entry: {signal['entry_price']}"
        
        return f"""
//@version=5
indicator("Auto Alert - Phase 1", overlay=true)

// エントリーレベル
entry_level = {signal['entry_price']}
stop_loss = {signal['stop_loss']}
take_profit = {signal['take_profit']}

// レベルをプロット
plot(entry_level, color=color.blue, title="Entry")
plot(stop_loss, color=color.red, title="Stop Loss")
plot(take_profit, color=color.green, title="Take Profit")

// アラート条件
alertcondition({condition}, title="{signal['action']} Alert", message="{alert_message}")
"""


async def setup_tradingview_alerts(analysis_results: Dict):
    """分析結果からTradingViewアラートを設定"""
    
    auto_alert = TradingViewAutoAlert()
    signal_generator = SignalGenerator()
    
    for currency, result in analysis_results.items():
        if result.get('success'):
            # シグナル生成
            signal = signal_generator.generate_trading_signal(result['analysis'])
            
            if signal['action'] != 'NONE' and signal['confidence'] >= 0.7:
                # TradingViewアラートを自動作成
                tv_currency = currency.replace('/', '')  # USD/JPY -> USDJPY
                await auto_alert.create_alert_from_signal(signal, tv_currency)
                
                logger.info(f"{currency}: TradingViewアラート設定完了")


# 使用例
async def main():
    """テスト実行"""
    
    # サンプルシグナル
    test_signal = {
        'action': 'BUY',
        'entry_price': 145.50,
        'stop_loss': 145.20,
        'take_profit': 146.00,
        'confidence': 0.85
    }
    
    # アラート自動作成
    auto_alert = TradingViewAutoAlert()
    await auto_alert.create_alert_from_signal(test_signal, "USDJPY")
    
    # Pine Script生成
    generator = PineScriptGenerator()
    script = generator.generate_alert_script(test_signal)
    print("Generated Pine Script:")
    print(script)


if __name__ == "__main__":
    asyncio.run(main())