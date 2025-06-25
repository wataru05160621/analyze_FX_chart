"""
Playwright経由でChatGPTのWebインターフェースを使用してプロジェクトにアクセスするモジュール
"""
import asyncio
from pathlib import Path
from typing import Dict, List
import logging
from playwright.async_api import async_playwright, Browser, Page
import base64
import time

logger = logging.getLogger(__name__)

class ChatGPTWebAnalyzer:
    """Playwright経由でChatGPTプロジェクトにアクセスするクラス"""
    
    def __init__(self, email: str, password: str, project_name: str):
        self.email = email
        self.password = password
        self.project_name = project_name
        self.browser = None
        self.page = None
        
    async def setup(self):
        """ブラウザの初期化とログイン"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # デバッグ時は False に設定
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        
        # ChatGPTにログイン
        await self._login()
        
        # プロジェクトを選択
        await self._select_project()
        
    async def _login(self):
        """ChatGPTにログイン"""
        try:
            logger.info("ChatGPTにログイン中...")
            await self.page.goto("https://chat.openai.com/")
            
            # ログインボタンをクリック
            await self.page.click('button:has-text("Log in")')
            await self.page.wait_for_timeout(2000)
            
            # メールアドレスを入力
            await self.page.fill('input[name="username"]', self.email)
            await self.page.click('button:has-text("Continue")')
            await self.page.wait_for_timeout(2000)
            
            # パスワードを入力
            await self.page.fill('input[name="password"]', self.password)
            await self.page.click('button:has-text("Continue")')
            
            # ログイン完了を待つ
            await self.page.wait_for_url("https://chat.openai.com/**", timeout=30000)
            logger.info("ログイン成功")
            
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            raise
            
    async def _select_project(self):
        """プロジェクトを選択"""
        try:
            logger.info(f"プロジェクト '{self.project_name}' を選択中...")
            
            # プロジェクト選択メニューを開く
            await self.page.wait_for_timeout(3000)
            
            # GPTセレクターをクリック
            await self.page.click('button[aria-label="Model selector"]')
            await self.page.wait_for_timeout(1000)
            
            # プロジェクトを検索して選択
            await self.page.fill('input[placeholder="Search"]', self.project_name)
            await self.page.wait_for_timeout(1000)
            
            # プロジェクトをクリック
            await self.page.click(f'text="{self.project_name}"')
            await self.page.wait_for_timeout(2000)
            
            logger.info("プロジェクト選択完了")
            
        except Exception as e:
            logger.error(f"プロジェクト選択エラー: {e}")
            raise
            
    async def analyze_charts(self, chart_images: Dict[str, Path], prompt: str) -> str:
        """チャート画像をアップロードして分析"""
        try:
            logger.info("チャート分析を開始...")
            
            # メッセージ入力エリアにフォーカス
            await self.page.click('textarea[placeholder*="Message"]')
            
            # プロンプトを入力
            await self.page.fill('textarea[placeholder*="Message"]', prompt)
            
            # 画像をアップロード
            for timeframe, image_path in chart_images.items():
                logger.info(f"{timeframe}チャートをアップロード中...")
                
                # ファイル入力要素を取得
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(str(image_path))
                    await self.page.wait_for_timeout(2000)
            
            # 送信ボタンをクリック
            await self.page.click('button[aria-label="Send message"]')
            
            # 応答を待つ
            logger.info("ChatGPTの応答を待機中...")
            await self.page.wait_for_timeout(5000)
            
            # 応答の完了を待つ（ストリーミングが終わるまで）
            previous_text = ""
            stable_count = 0
            
            while stable_count < 3:
                await self.page.wait_for_timeout(2000)
                
                # 最新のメッセージを取得
                messages = await self.page.query_selector_all('.prose')
                if messages:
                    current_text = await messages[-1].inner_text()
                    
                    if current_text == previous_text:
                        stable_count += 1
                    else:
                        stable_count = 0
                        previous_text = current_text
            
            # 最終的な応答を取得
            final_response = previous_text
            logger.info(f"分析完了: {len(final_response)}文字")
            
            return final_response
            
        except Exception as e:
            logger.error(f"チャート分析エラー: {e}")
            raise
            
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()