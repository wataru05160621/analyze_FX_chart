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
    
    def __init__(self):
        from .config import CHATGPT_EMAIL, CHATGPT_PASSWORD, CHATGPT_PROJECT_NAME
        self.email = CHATGPT_EMAIL
        self.password = CHATGPT_PASSWORD
        self.project_name = CHATGPT_PROJECT_NAME
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
        """ChatGPTにログイン（Google認証対応）"""
        try:
            logger.info("ChatGPTにログイン中...")
            await self.page.goto("https://chat.openai.com/")
            await self.page.wait_for_timeout(3000)
            
            # ログインボタンをクリック
            login_button = await self.page.query_selector('button:has-text("Log in"), a:has-text("Log in")')
            if login_button:
                await login_button.click()
                await self.page.wait_for_timeout(3000)
            
            # Googleでログインボタンを探してクリック
            google_button = await self.page.query_selector('button:has-text("Continue with Google"), button[data-provider="google"]')
            if google_button:
                logger.info("Googleログインボタンを発見、クリック中...")
                await google_button.click()
                await self.page.wait_for_timeout(3000)
                
                # Google認証ページでメールアドレスを入力
                email_input = await self.page.query_selector('input[type="email"], input[name="identifier"]')
                if email_input:
                    await email_input.fill(self.email)
                    await self.page.wait_for_timeout(1000)
                    
                    # 次へボタンをクリック
                    next_button = await self.page.query_selector('button:has-text("次へ"), button[id="identifierNext"], button:has-text("Next")')
                    if next_button:
                        await next_button.click()
                        await self.page.wait_for_timeout(3000)
                
                # パスワードを入力
                password_input = await self.page.query_selector('input[type="password"], input[name="password"]')
                if password_input:
                    await password_input.fill(self.password)
                    await self.page.wait_for_timeout(1000)
                    
                    # 次へ/ログインボタンをクリック
                    login_submit = await self.page.query_selector('button:has-text("次へ"), button[id="passwordNext"], button:has-text("Next")')
                    if login_submit:
                        await login_submit.click()
                        await self.page.wait_for_timeout(5000)
            else:
                # 通常のメールログインの場合
                logger.info("通常のメールログインを試行中...")
                email_input = await self.page.query_selector('input[name="username"], input[type="email"]')
                if email_input:
                    await email_input.fill(self.email)
                    continue_button = await self.page.query_selector('button:has-text("Continue")')
                    if continue_button:
                        await continue_button.click()
                        await self.page.wait_for_timeout(2000)
                
                password_input = await self.page.query_selector('input[name="password"], input[type="password"]')
                if password_input:
                    await password_input.fill(self.password)
                    continue_button = await self.page.query_selector('button:has-text("Continue")')
                    if continue_button:
                        await continue_button.click()
            
            # ログイン完了を待つ
            await self.page.wait_for_timeout(10000)
            
            # ChatGPTメインページに到達したかチェック
            current_url = self.page.url
            if "chat.openai.com" in current_url:
                logger.info("ログイン成功")
            else:
                logger.warning(f"ログイン後のURL確認: {current_url}")
            
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            raise
            
    async def _select_project(self):
        """プロジェクトを選択"""
        try:
            logger.info(f"プロジェクト '{self.project_name}' を選択中...")
            
            # プロジェクト選択メニューを開く
            await self.page.wait_for_timeout(5000)
            
            # 複数のセレクタを試行
            selectors = [
                'button[aria-label="Model selector"]',
                'button:has-text("ChatGPT")',
                'button:has-text("GPT")',
                '[data-testid="model-switcher"]',
                'div[data-testid="chat-model-selector"]',
                'button[data-testid="model-selector-button"]',
                'select[data-testid="model-select"]'
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        logger.info(f"モデルセレクタを発見: {selector}")
                        await element.click()
                        await self.page.wait_for_timeout(2000)
                        clicked = True
                        break
                except Exception as e:
                    logger.debug(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not clicked:
                logger.warning("モデルセレクタが見つかりません。プロジェクト選択をスキップします。")
                return
            
            # プロジェクトを検索して選択
            search_selectors = [
                'input[placeholder="Search"]',
                'input[placeholder="検索"]',
                'input[type="search"]',
                'input[role="searchbox"]'
            ]
            
            searched = False
            for search_selector in search_selectors:
                try:
                    search_input = await self.page.query_selector(search_selector)
                    if search_input:
                        await search_input.fill(self.project_name)
                        await self.page.wait_for_timeout(1000)
                        searched = True
                        break
                except Exception as e:
                    logger.debug(f"検索入力 {search_selector} でエラー: {e}")
                    continue
            
            # プロジェクトをクリック
            project_selectors = [
                f'text="{self.project_name}"',
                f'div:has-text("{self.project_name}")',
                f'button:has-text("{self.project_name}")',
                f'[data-testid*="project"]:has-text("{self.project_name}")'
            ]
            
            project_found = False
            for project_selector in project_selectors:
                try:
                    project_element = await self.page.query_selector(project_selector)
                    if project_element:
                        await project_element.click()
                        await self.page.wait_for_timeout(2000)
                        project_found = True
                        logger.info("プロジェクト選択完了")
                        break
                except Exception as e:
                    logger.debug(f"プロジェクト選択 {project_selector} でエラー: {e}")
                    continue
            
            if not project_found:
                logger.warning(f"プロジェクト '{self.project_name}' が見つかりません。デフォルトのGPTを使用します。")
            
        except Exception as e:
            logger.error(f"プロジェクト選択エラー: {e}")
            logger.warning("プロジェクト選択に失敗しましたが、処理を続行します。")
            
    async def analyze_charts(self, chart_images: Dict[str, Path], prompt: str) -> str:
        """チャート画像をアップロードして分析"""
        try:
            logger.info("チャート分析を開始...")
            
            # まず新しいチャットを開始するため、チャットページに移動
            await self.page.goto("https://chatgpt.com/")
            await self.page.wait_for_timeout(5000)
            
            # ページの読み込み完了を待つ
            try:
                await self.page.wait_for_selector('textarea, input[type="text"], div[contenteditable="true"]', timeout=30000)
            except Exception as e:
                logger.warning(f"入力要素の読み込み待機でタイムアウト: {e}")
                # さらに待機
                await self.page.wait_for_timeout(10000)
            
            # メッセージ入力エリアを見つける
            input_selectors = [
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="メッセージ"]',
                'textarea[data-testid="prompt-textarea"]',
                'textarea[id="prompt-textarea"]',
                'div[contenteditable="true"]',
                'textarea',
                'input[type="text"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        logger.info(f"入力エリアを発見: {selector}")
                        input_element = element
                        break
                except Exception as e:
                    logger.debug(f"セレクタ {selector} でエラー: {e}")
                    continue
            
            if not input_element:
                # スクリーンショットを取得してデバッグ
                await self.page.screenshot(path="debug_chatgpt.png")
                logger.error("メッセージ入力エリアが見つかりません")
                raise Exception("メッセージ入力エリアが見つかりません")
            
            # プロンプトを入力
            await input_element.click()
            await self.page.wait_for_timeout(1000)
            await input_element.fill(prompt)
            
            # 画像をアップロード
            for timeframe, image_path in chart_images.items():
                logger.info(f"{timeframe}チャートをアップロード中...")
                
                # アップロードボタンを探す
                upload_selectors = [
                    'input[type="file"]',
                    'button[aria-label="Attach files"]',
                    'button[data-testid="attachment-button"]',
                    '[data-testid="file-upload"]'
                ]
                
                uploaded = False
                for upload_selector in upload_selectors:
                    try:
                        upload_element = await self.page.query_selector(upload_selector)
                        if upload_element:
                            if upload_selector == 'input[type="file"]':
                                await upload_element.set_input_files(str(image_path))
                            else:
                                await upload_element.click()
                                await self.page.wait_for_timeout(1000)
                                file_input = await self.page.query_selector('input[type="file"]')
                                if file_input:
                                    await file_input.set_input_files(str(image_path))
                            uploaded = True
                            await self.page.wait_for_timeout(2000)
                            break
                    except Exception as e:
                        logger.debug(f"アップロード {upload_selector} でエラー: {e}")
                        continue
                
                if not uploaded:
                    logger.warning(f"{timeframe}チャートのアップロードに失敗しました")
            
            # 送信ボタンをクリック
            send_selectors = [
                'button[aria-label="Send message"]',
                'button[data-testid="send-button"]',
                'button:has-text("Send")',
                'button:has-text("送信")',
                '[data-testid="send"]'
            ]
            
            sent = False
            for send_selector in send_selectors:
                try:
                    send_button = await self.page.query_selector(send_selector)
                    if send_button:
                        await send_button.click()
                        sent = True
                        break
                except Exception as e:
                    logger.debug(f"送信ボタン {send_selector} でエラー: {e}")
                    continue
            
            if not sent:
                # Enterキーで送信を試行
                await input_element.press('Enter')
            
            # 応答を待つ
            logger.info("ChatGPTの応答を待機中...")
            await self.page.wait_for_timeout(10000)
            
            # 応答の完了を待つ（ストリーミングが終わるまで）
            previous_text = ""
            stable_count = 0
            max_wait = 30  # 最大30回（60秒）
            wait_count = 0
            
            while stable_count < 3 and wait_count < max_wait:
                await self.page.wait_for_timeout(2000)
                wait_count += 1
                
                # 最新のメッセージを取得
                message_selectors = [
                    '.prose',
                    '[data-testid="conversation-turn-content"]',
                    '.markdown',
                    '.message-content',
                    '.text-base'
                ]
                
                current_text = ""
                for msg_selector in message_selectors:
                    try:
                        messages = await self.page.query_selector_all(msg_selector)
                        if messages:
                            current_text = await messages[-1].inner_text()
                            break
                    except Exception as e:
                        logger.debug(f"メッセージ取得 {msg_selector} でエラー: {e}")
                        continue
                
                if current_text == previous_text and current_text:
                    stable_count += 1
                else:
                    stable_count = 0
                    previous_text = current_text
            
            # 最終的な応答を取得
            final_response = previous_text if previous_text else "応答を取得できませんでした"
            logger.info(f"分析完了: {len(final_response)}文字")
            
            return final_response
            
        except Exception as e:
            logger.error(f"チャート分析エラー: {e}")
            raise
            
    async def close(self):
        """ブラウザを閉じる"""
        if self.browser:
            await self.browser.close()