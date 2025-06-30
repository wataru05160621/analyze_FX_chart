"""
Notion APIを使用して分析結果を保存するモジュール
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from notion_client import Client
import requests
from .config import NOTION_API_KEY, NOTION_DATABASE_ID
from .image_uploader import get_uploader

logger = logging.getLogger(__name__)

class NotionWriter:
    """Notion APIを使用して分析結果を保存するクラス"""
    
    def __init__(self):
        self.client = Client(auth=NOTION_API_KEY)
        self.database_id = NOTION_DATABASE_ID
        
    def create_analysis_page(self, title: str, analysis: str, chart_images: Dict[str, Path]) -> str:
        """分析結果をNotionページとして作成"""
        try:
            # ページのプロパティを設定
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                },
                "Status": {
                    "status": {
                        "name": "完了"
                    }
                },
                "Currency": {
                    "multi_select": [
                        {
                            "name": "USD/JPY"
                        }
                    ]
                }
            }
            
            # ページを作成
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            page_id = page["id"]
            logger.info(f"Notionページを作成しました: {page_id}")
            
            # コンテンツを追加
            self._add_content_blocks(page_id, analysis, chart_images)
            
            return page_id
            
        except Exception as e:
            logger.error(f"Notionページ作成エラー: {e}")
            raise
            
    def _add_content_blocks(self, page_id: str, analysis: str, chart_images: Dict[str, Path]):
        """ページにコンテンツブロックを追加"""
        blocks = []
        
        # タイトル
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "📊 FXチャート分析結果"
                        }
                    }
                ]
            }
        })
        
        # 分析日時
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}"
                        }
                    }
                ]
            }
        })
        
        # チャート画像セクション
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "チャート画像"
                        }
                    }
                ]
            }
        })
        
        # 各チャート画像をアップロード
        for timeframe, image_path in chart_images.items():
            # 画像をアップロード
            image_url = self._upload_image(image_path)
            if image_url:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{timeframe}チャート:"
                                },
                                "annotations": {
                                    "bold": True
                                }
                            }
                        ]
                    }
                })
                
                blocks.append({
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {
                            "url": image_url
                        }
                    }
                })
        
        # 分析結果セクション
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "分析結果"
                        }
                    }
                ]
            }
        })
        
        # 分析結果を段落に分割
        analysis_paragraphs = analysis.split('\n\n')
        for paragraph in analysis_paragraphs:
            if paragraph.strip():
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": paragraph.strip()
                                }
                            }
                        ]
                    }
                })
        
        # ブロックを追加
        try:
            self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )
            logger.info("コンテンツブロックを追加しました")
        except Exception as e:
            logger.error(f"ブロック追加エラー: {e}")
            raise
            
    def _upload_image(self, image_path: Path) -> str:
        """画像をアップロードしてURLを返す"""
        logger.info(f"画像アップロード開始: {image_path}")
        uploader = get_uploader()
        
        if uploader:
            logger.info(f"アップローダー取得成功: {type(uploader).__name__}")
            url = uploader.upload(image_path)
            if url:
                logger.info(f"画像アップロード成功: {url}")
                return url
            else:
                logger.error("画像アップロードに失敗しました")
        else:
            logger.warning("アップローダーが取得できませんでした")
        
        # アップローダーが設定されていない場合のフォールバック
        logger.warning(f"画像アップロードが設定されていません。ローカルパスを使用: {image_path}")
        return f"file://{image_path.absolute()}"
        
    def create_database(self, parent_page_id: str):
        """分析結果を保存するためのデータベースを作成"""
        try:
            database = self.client.databases.create(
                parent={"page_id": parent_page_id},
                title=[
                    {
                        "type": "text",
                        "text": {
                            "content": "FX分析結果"
                        }
                    }
                ],
                properties={
                    "Name": {
                        "title": {}
                    },
                    "Date": {
                        "date": {}
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "分析中", "color": "yellow"},
                                {"name": "完了", "color": "green"},
                                {"name": "エラー", "color": "red"}
                            ]
                        }
                    },
                    "Currency": {
                        "select": {
                            "options": [
                                {"name": "USD/JPY", "color": "blue"},
                                {"name": "EUR/USD", "color": "purple"},
                                {"name": "GBP/USD", "color": "pink"}
                            ]
                        }
                    },
                    "Timeframe": {
                        "multi_select": {
                            "options": [
                                {"name": "5分足", "color": "gray"},
                                {"name": "1時間足", "color": "brown"},
                                {"name": "4時間足", "color": "orange"},
                                {"name": "日足", "color": "green"}
                            ]
                        }
                    }
                }
            )
            
            logger.info(f"データベースを作成しました: {database['id']}")
            return database['id']
            
        except Exception as e:
            logger.error(f"データベース作成エラー: {e}")
            raise