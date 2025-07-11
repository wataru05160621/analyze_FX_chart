"""
WordPress + X (Twitter) 自動投稿モジュール
"""
import requests
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import re
import tweepy
from pathlib import Path
import base64
import os

logger = logging.getLogger(__name__)

class BlogPublisher:
    """ブログとSNSへの自動投稿を管理するクラス"""
    
    def __init__(self, wordpress_config: Dict, twitter_config: Dict):
        """
        Args:
            wordpress_config: WordPressの設定
                - url: WordPressサイトのURL
                - username: ユーザー名
                - password: アプリケーションパスワード
            twitter_config: Twitter/Xの設定
                - api_key: API Key
                - api_secret: API Secret
                - access_token: Access Token
                - access_token_secret: Access Token Secret
        """
        self.wp_config = wordpress_config
        self.twitter_config = twitter_config
        
        # WordPress認証ヘッダー作成
        credentials = f"{wordpress_config['username']}:{wordpress_config['password']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.wp_headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        # Twitter API v1.1とv2の両方を初期化
        # v1.1 API（一時的な回避策）
        auth = tweepy.OAuthHandler(
            twitter_config['api_key'],
            twitter_config['api_secret']
        )
        auth.set_access_token(
            twitter_config['access_token'],
            twitter_config['access_token_secret']
        )
        self.twitter_api_v1 = tweepy.API(auth)
        
        # v2 API（将来的に使用）
        self.twitter_client = tweepy.Client(
            consumer_key=twitter_config['api_key'],
            consumer_secret=twitter_config['api_secret'],
            access_token=twitter_config['access_token'],
            access_token_secret=twitter_config['access_token_secret']
        )
        
    def upload_media_to_wordpress(self, image_path: Path) -> Optional[Dict]:
        """WordPress メディアライブラリに画像をアップロード"""
        try:
            url = f"{self.wp_config['url']}/wp-json/wp/v2/media"
            
            with open(image_path, 'rb') as img:
                files = {
                    'file': (image_path.name, img, 'image/png')
                }
                headers = {
                    'Authorization': self.wp_headers['Authorization']
                }
                
                response = requests.post(url, files=files, headers=headers)
                response.raise_for_status()
                
                media_data = response.json()
                logger.info(f"画像アップロード成功: ID={media_data['id']}, URL={media_data['source_url']}")
                return media_data
                
        except Exception as e:
            logger.error(f"画像アップロードエラー: {e}")
            return None
    
    def format_analysis_for_blog(self, analysis: str, chart_paths: Dict[str, Path]) -> Tuple[str, str]:
        """分析結果をブログ記事用にフォーマット"""
        
        # タイトル生成（日付を含む）
        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"【USD/JPY】{today} 朝の相場分析"
        
        # 本文フォーマット
        content = f"""
<p>おはようございます。本日の<strong>USD/JPY（ドル円）</strong>相場分析をお届けします。</p>

<h2>チャート画像</h2>
<!-- チャート画像はここに挿入されます -->

<h2>詳細分析</h2>
<div class="analysis-content">
{self._convert_markdown_to_html(analysis)}
</div>

<hr>

<p><small>※本分析は参考情報であり、投資判断は自己責任でお願いいたします。</small></p>
<p><small>分析システム: Claude 3.5 Sonnet + Python自動分析</small></p>
"""
        
        return title, content
    
    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """Markdownを簡易的にHTMLに変換"""
        html = markdown_text
        
        # 見出し変換
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # 強調
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # リスト
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>\n)+', r'<ul>\g<0></ul>', html, flags=re.MULTILINE)
        
        # 段落
        html = '<p>' + html.replace('\n\n', '</p><p>') + '</p>'
        
        # テーブル（簡易版）
        html = re.sub(r'\|(.+)\|', r'<table class="analysis-table"><tr>\1</tr></table>', html)
        
        return html
    
    def publish_to_wordpress(self, analysis: str, chart_paths: Dict[str, Path]) -> Optional[str]:
        """WordPressに記事を投稿"""
        try:
            # 記事フォーマット
            title, content = self.format_analysis_for_blog(analysis, chart_paths)
            
            # 画像アップロード（5分足と1時間足）
            media_data_list = []
            timeframe_labels = {'5min': '5分足チャート', '1hour': '1時間足チャート'}
            
            for timeframe in ['5min', '1hour']:
                if timeframe in chart_paths:
                    media_data = self.upload_media_to_wordpress(chart_paths[timeframe])
                    if media_data:
                        media_data['timeframe'] = timeframe
                        media_data['label'] = timeframe_labels[timeframe]
                        media_data_list.append(media_data)
            
            # 画像をコンテンツに挿入
            if media_data_list:
                image_html = ""
                for media in media_data_list:
                    image_html += f'''
<figure class="wp-block-image size-full">
<img src="{media['source_url']}" alt="{media['label']}" class="wp-image-{media['id']}"/>
<figcaption>{media['label']}</figcaption>
</figure>
'''
                content = content.replace("<!-- チャート画像はここに挿入されます -->", image_html)
            
            # カテゴリとタグのID（環境変数から取得）
            category_ids = []
            if os.getenv("WORDPRESS_CATEGORY_USDJPY"):
                category_ids.append(int(os.getenv("WORDPRESS_CATEGORY_USDJPY")))
            if os.getenv("WORDPRESS_CATEGORY_ANALYSIS"):
                category_ids.append(int(os.getenv("WORDPRESS_CATEGORY_ANALYSIS")))
            
            tag_ids = []
            if os.getenv("WORDPRESS_TAG_DAILY_USDJPY"):
                tag_ids.append(int(os.getenv("WORDPRESS_TAG_DAILY_USDJPY")))
            
            # 記事データ
            post_data = {
                'title': title,
                'content': content,
                'status': 'publish',
                'categories': category_ids,  # カテゴリーID
                'tags': tag_ids,  # タグID
                'featured_media': media_data_list[0]['id'] if media_data_list else 0  # アイキャッチ画像
            }
            
            # 投稿
            url = f"{self.wp_config['url']}/wp-json/wp/v2/posts"
            response = requests.post(url, headers=self.wp_headers, json=post_data)
            response.raise_for_status()
            
            post_url = response.json()['link']
            logger.info(f"WordPress投稿成功: {post_url}")
            return post_url
            
        except Exception as e:
            logger.error(f"WordPress投稿エラー: {e}")
            return None
    
    def extract_summary_for_twitter(self, analysis: str) -> str:
        """分析結果からTwitter用の要約を抽出（教育的内容）"""
        
        # 重要な情報を抽出
        summary_parts = []
        
        # 現在価格を探す
        price_match = re.search(r'現在価格[：:]\s*([\d.]+)', analysis)
        if price_match:
            summary_parts.append(f"USD/JPY: {price_match.group(1)}円")
        
        # EMA配列を探す
        if "25EMA > 75EMA > 200EMA" in analysis:
            summary_parts.append("📈EMA上昇配列")
        elif "25EMA < 75EMA < 200EMA" in analysis:
            summary_parts.append("📉EMA下降配列")
        else:
            summary_parts.append("📊EMA混在状態")
        
        # ビルドアップ状況を探す
        if "教科書的な完璧な形状" in analysis:
            summary_parts.append("⭐完璧なビルドアップ観察")
        elif "良好な形状" in analysis:
            summary_parts.append("✨良好なビルドアップ")
        elif "ビルドアップ" in analysis:
            summary_parts.append("📊ビルドアップ形成中")
        
        # Volmanセットアップを探す
        if "パターンブレイク" in analysis:
            summary_parts.append("📊Volmanパターンブレイク")
        elif "ビルドアップ" in analysis:
            summary_parts.append("📈ビルドアップ形成中")
        elif "25EMA" in analysis:
            summary_parts.append("📉25EMAサポート/レジスタンス")
        
        # 基本テンプレート
        base_text = f"【{datetime.now().strftime('%m/%d')} USD/JPY チャート解説】\n"
        base_text += "\n".join(summary_parts[:3])  # 最大3項目まで
        base_text += "\n\nVolmanスキャルピングメソッドに基づく教育的解説"
        
        # ハッシュタグ（短めに設定）
        hashtags = "\n\n#USDJPY #ドル円 #FX学習 #Volmanメソッド #スキャルピング"
        
        # 文字数調整（URLとリンクテキスト分の余裕を持たせる：約50文字）
        max_length = 200  # URL + "詳細分析はこちら👇\n" の分を考慮
        if len(base_text + hashtags) > max_length:
            base_text = base_text[:max_length - len(hashtags)]
        
        return base_text + hashtags
    
    def publish_to_twitter(self, analysis: str, blog_url: Optional[str] = None) -> Optional[str]:
        """X (Twitter)に投稿"""
        try:
            # 要約作成
            summary = self.extract_summary_for_twitter(analysis)
            
            # ブログURLを追加
            if blog_url:
                tweet_text = f"{summary}\n\n詳細分析はこちら👇\n{blog_url}"
            else:
                tweet_text = summary
            
            # ツイート（v1.1 APIを使用）
            try:
                # まずv2 APIを試す
                response = self.twitter_client.create_tweet(text=tweet_text)
                
                if response.data:
                    tweet_id = response.data['id']
                    tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                    logger.info(f"Twitter投稿成功: {tweet_url}")
                    return tweet_url
            except Exception as v2_error:
                logger.warning(f"v2 API失敗、v1.1 APIで再試行: {v2_error}")
                
                # v1.1 APIで再試行
                tweet = self.twitter_api_v1.update_status(tweet_text)
                tweet_url = f"https://twitter.com/user/status/{tweet.id}"
                logger.info(f"Twitter投稿成功 (v1.1 API): {tweet_url}")
                return tweet_url
            
        except Exception as e:
            logger.error(f"Twitter投稿エラー: {e}")
            return None
    
    def publish_analysis(self, analysis: str, chart_paths: Dict[str, Path]) -> Dict[str, Optional[str]]:
        """分析結果をWordPressとTwitterに投稿"""
        
        results = {
            'wordpress_url': None,
            'twitter_url': None
        }
        
        # チャートパスのデバッグ情報
        logger.info(f"受け取ったチャートパス: {chart_paths}")
        for timeframe, path in chart_paths.items():
            if isinstance(path, Path):
                logger.info(f"  {timeframe}: {path} (存在: {path.exists()})")
            else:
                logger.warning(f"  {timeframe}: パスがPath型ではありません: {type(path)}")
        
        # WordPressに投稿
        blog_url = self.publish_to_wordpress(analysis, chart_paths)
        results['wordpress_url'] = blog_url
        
        # Twitterに投稿（ブログURLを含む）
        if blog_url:
            twitter_url = self.publish_to_twitter(analysis, blog_url)
            results['twitter_url'] = twitter_url
        
        return results