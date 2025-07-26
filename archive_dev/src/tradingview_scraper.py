"""
Trading Viewのチャートをスクリーンショット取得するモジュール
"""
import asyncio
from pathlib import Path
from typing import Dict
import logging
from playwright.async_api import async_playwright, Browser, Page
from datetime import datetime
import time
from src.config import TRADINGVIEW_USERNAME, TRADINGVIEW_PASSWORD

logger = logging.getLogger(__name__)

class TradingViewScraper:
    """Trading Viewからチャートのスクリーンショットを取得するクラス"""
    
    def __init__(self, chart_url: str = None):
        """
        Args:
            chart_url: カスタムチャートURL（指定しない場合はデフォルトURL使用）
        """
        self.chart_url = chart_url or "https://jp.tradingview.com/chart/"
        self.browser = None
        self.page = None
        
    async def setup(self):
        """ブラウザの初期化"""
        playwright = await async_playwright().start()
        
        # Docker環境でのブラウザパス設定
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
        ]
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=browser_args,
            executable_path=None  # 自動検出を使用
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='ja-JP'
        )
        
        self.page = await context.new_page()
        
    async def navigate_to_chart(self, custom_url: str = None):
        """チャートページへ移動"""
        try:
            url = custom_url or self.chart_url
            logger.info(f"チャートページへ移動: {url}")
            
            await self.page.goto(url, wait_until="networkidle")
            await self.page.wait_for_timeout(8000)  # チャート読み込み待機時間を延長
            
            # ポップアップやCookieバナーを閉じる
            await self._close_popups()
            
            # ログインが必要な場合はログイン
            if TRADINGVIEW_USERNAME and TRADINGVIEW_PASSWORD:
                await self._login()
            
            logger.info("チャートページの読み込み完了")
            
        except Exception as e:
            logger.error(f"ページ移動エラー: {e}")
            raise
            
    async def _close_popups(self):
        """ポップアップやバナーを閉じる"""
        try:
            # Cookieバナーを閉じる
            cookie_button = await self.page.query_selector('button:has-text("同意する")')
            if cookie_button:
                await cookie_button.click()
                await self.page.wait_for_timeout(1000)
                
            # その他のポップアップを閉じる
            close_buttons = await self.page.query_selector_all('button[aria-label="閉じる"], button[aria-label="Close"]')
            for button in close_buttons:
                try:
                    await button.click()
                    await self.page.wait_for_timeout(500)
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"ポップアップ処理中のエラー（無視）: {e}")
    
    async def _login(self):
        """Trading Viewにログイン"""
        try:
            logger.info("Trading Viewへのログインを試行中...")
            
            # ログイン画面が既に表示されているかチェック
            login_form = await self.page.query_selector('form:has(input[type="password"])')
            
            if login_form:
                logger.info("ログインフォームが検出されました")
                
                # ユーザー名入力（既に入力されている場合があるので、クリアしてから入力）
                username_input = await self.page.query_selector('input[name="username"], input[type="text"]:not([type="password"])')
                if username_input:
                    await username_input.click()
                    await username_input.fill("")  # クリア
                    await username_input.fill(TRADINGVIEW_USERNAME)
                    await self.page.wait_for_timeout(500)
                    logger.info("ユーザー名を入力しました")
                
                # パスワード入力
                password_input = await self.page.query_selector('input[type="password"]')
                if password_input:
                    await password_input.click()
                    await password_input.fill("")  # クリア
                    await password_input.fill(TRADINGVIEW_PASSWORD)
                    await self.page.wait_for_timeout(500)
                    logger.info("パスワードを入力しました")
                
                # ログインボタンをクリック
                login_button = await self.page.query_selector('button:has-text("ログイン"), button[type="submit"]')
                if login_button:
                    await login_button.click()
                    logger.info("ログインボタンをクリックしました")
                    await self.page.wait_for_timeout(5000)  # ログイン処理を待つ
                    
                    # ログイン成功の確認
                    await self.page.wait_for_timeout(3000)
                    logger.info("Trading Viewへのログイン処理完了")
            else:
                # ログインボタンを探す
                login_button = await self.page.query_selector('button:has-text("ログイン"), button:has-text("Sign in"), [data-name="header-user-menu-sign-in"]')
                if login_button:
                    await login_button.click()
                    await self.page.wait_for_timeout(3000)
                    
                    # Eメールでログインを選択
                    email_login = await self.page.query_selector('button:has-text("Eメール"), button:has-text("Email")')
                    if email_login:
                        await email_login.click()
                        await self.page.wait_for_timeout(2000)
                    
                    # 再帰的にログイン処理を実行
                    await self._login()
                else:
                    logger.info("既にログイン済みか、ログインボタンが見つかりません")
                
        except Exception as e:
            logger.warning(f"ログイン処理中のエラー: {e}")
            # ログインに失敗してもスクリーンショット取得は続行
            
    async def set_timeframe(self, timeframe: str):
        """時間足を設定"""
        try:
            logger.info(f"時間足を{timeframe}に設定中...")
            
            # 時間足セレクターをクリック
            await self.page.click('button[aria-label="時間足を変更"]')
            await self.page.wait_for_timeout(1000)
            
            # 時間足を選択
            timeframe_map = {
                "5": "5分",
                "60": "1時間",
                "240": "4時間",
                "D": "1日"
            }
            
            timeframe_text = timeframe_map.get(timeframe, timeframe)
            await self.page.click(f'div[role="menuitem"]:has-text("{timeframe_text}")')
            await self.page.wait_for_timeout(2000)
            
            logger.info(f"時間足を{timeframe_text}に設定完了")
            
        except Exception as e:
            logger.error(f"時間足設定エラー: {e}")
            # エラーが発生してもスクリーンショットは取得を試みる
            
    async def capture_screenshot(self, output_path: Path):
        """チャートのスクリーンショットを取得"""
        try:
            logger.info(f"スクリーンショットを取得中: {output_path}")
            
            # チャートエリアを特定
            chart_element = await self.page.query_selector('.chart-container, #chart-area, .chart-widget')
            
            if chart_element:
                # チャートエリアのみをキャプチャ
                await chart_element.screenshot(path=str(output_path))
            else:
                # フルページをキャプチャ
                await self.page.screenshot(path=str(output_path), full_page=False)
                
            logger.info(f"スクリーンショット保存完了: {output_path}")
            
        except Exception as e:
            logger.error(f"スクリーンショット取得エラー: {e}")
            raise
            
    async def capture_charts(self, timeframes: Dict[str, str], output_dir: Path) -> Dict[str, Path]:
        """複数の時間足のチャートをキャプチャ"""
        screenshots = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for name, timeframe in timeframes.items():
            try:
                # 時間足を設定
                await self.set_timeframe(timeframe)
                
                # スクリーンショットを保存
                filename = f"chart_{name}_{timestamp}.png"
                output_path = output_dir / filename
                await self.capture_screenshot(output_path)
                
                screenshots[name] = output_path
                
            except Exception as e:
                logger.error(f"{name}のキャプチャに失敗: {e}")
                
        return screenshots
        
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()