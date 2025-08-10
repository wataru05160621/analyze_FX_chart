"""Notion integration for analysis results."""

from datetime import datetime
from typing import Dict, List, Optional
from notion_client import Client

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class NotionClient:
    """Notion client for storing analysis results."""
    
    def __init__(self, api_key: Optional[str] = None, db_id: Optional[str] = None):
        """Initialize Notion client."""
        self.api_key = api_key or config.notion_api_key
        self.db_id = db_id or config.notion_db_id
        
        if not self.api_key:
            raise ValueError("NOTION_API_KEY is required")
        if not self.db_id:
            raise ValueError("NOTION_DB_ID is required")
        
        self.client = Client(auth=self.api_key)
        
    def create_page(
        self,
        analysis: Dict,
        chart_urls: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a Notion page with analysis results.
        
        Args:
            analysis: Analysis results dict
            chart_urls: Dict of timeframe to pre-signed chart URLs
            
        Returns:
            Created page ID
        """
        # Prepare properties
        properties = self._prepare_properties(analysis)
        
        # Prepare content blocks
        blocks = self._prepare_blocks(analysis, chart_urls)
        
        try:
            # Create page
            response = self.client.pages.create(
                parent={"database_id": self.db_id},
                properties=properties,
                children=blocks
            )
            
            page_id = response["id"]
            page_url = response.get("url", "")
            
            logger.info(f"Created Notion page", page_id=page_id, url=page_url)
            
            return page_id
            
        except Exception as e:
            logger.error(f"Failed to create Notion page", error=str(e))
            raise
    
    def _prepare_properties(self, analysis: Dict) -> Dict:
        """Prepare page properties from analysis."""
        run_id = analysis.get("run_id", "unknown")
        timestamp = analysis.get("timestamp_jst", datetime.now().isoformat())
        pair = analysis.get("pair", config.pair)
        setup = analysis.get("final_setup", "No-Trade")
        confidence = analysis.get("confidence", "low")
        ev_r = analysis.get("ev_R", 0.0)
        
        # Format title
        title = f"{pair} | {setup} | {timestamp[:16]}"
        
        # Notionデータベースのプロパティに合わせて修正
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
                    "start": timestamp
                }
            },
            "Status": {
                "status": {
                    "name": "Done" if setup != "No-Trade" else "Not started"
                }
            },
            "Currency": {
                "multi_select": [
                    {
                        "name": pair
                    }
                ]
            }
        }
        
        return properties
    
    def _prepare_blocks(
        self,
        analysis: Dict,
        chart_urls: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """Prepare content blocks for the page."""
        blocks = []
        
        # Header
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": f"FX Analysis - {analysis.get('pair', 'USDJPY')}"
                    }
                }]
            }
        })
        
        # Summary section
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": "Summary"
                    }
                }]
            }
        })
        
        # Key metrics
        metrics = [
            f"Setup: {analysis.get('final_setup', 'No-Trade')}",
            f"Confidence: {analysis.get('confidence', 'low')}",
            f"Expected Value: {analysis.get('ev_R', 0):.2f}R",
            f"Status: {analysis.get('status', 'analyzed')}"
        ]
        
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": " | ".join(metrics)
                    }
                }]
            }
        })
        
        # Rationale section
        if "rationale" in analysis and analysis["rationale"]:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "Analysis Rationale"
                        }
                    }]
                }
            })
            
            for reason in analysis["rationale"][:10]:  # Limit to 10 items
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{
                            "type": "text",
                            "text": {
                                "content": reason
                            }
                        }]
                    }
                })
        
        # Charts section with images
        if chart_urls:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "Charts"
                        }
                    }]
                }
            })
            
            # Add image blocks for each chart
            for timeframe, url in chart_urls.items():
                # Add timeframe label
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{
                            "type": "text",
                            "text": {
                                "content": f"{timeframe} Chart"
                            }
                        }]
                    }
                })
                
                # Add image block
                blocks.append({
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {
                            "url": url
                        }
                    }
                })
        
        # Timeframe details
        if "timeframes" in analysis:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "Timeframe Analysis"
                        }
                    }]
                }
            })
            
            for tf, tf_data in analysis["timeframes"].items():
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{
                            "type": "text",
                            "text": {
                                "content": f"{tf} Analysis"
                            }
                        }]
                    }
                })
                
                if "indicators" in tf_data:
                    indicators = tf_data["indicators"]
                    indicator_text = []
                    
                    if "current_price" in indicators:
                        indicator_text.append(f"Price: {indicators['current_price']:.3f}")
                    if "ema25_slope_deg" in indicators:
                        indicator_text.append(f"EMA Slope: {indicators['ema25_slope_deg']}°")
                    if "atr20" in indicators:
                        indicator_text.append(f"ATR20: {indicators['atr20']}p")
                    
                    if indicator_text:
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{
                                    "type": "text",
                                    "text": {
                                        "content": " | ".join(indicator_text)
                                    }
                                }]
                            }
                        })
        
        # Trade plan if available
        if "plan" in analysis and analysis["plan"]:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": "Trade Plan"
                        }
                    }]
                }
            })
            
            plan = analysis["plan"]
            plan_text = []
            
            for key, value in plan.items():
                if value is not None:
                    plan_text.append(f"{key}: {value}")
            
            if plan_text:
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{
                            "type": "text",
                            "text": {
                                "content": "\n".join(plan_text)
                            }
                        }],
                        "language": "plain text"
                    }
                })
        
        return blocks
    
    def update_analysis_result(
        self,
        analysis: Dict,
        s3_results: Optional[Dict] = None
    ) -> str:
        """
        Create or update Notion page with analysis and S3 URLs.
        
        Args:
            analysis: Analysis results
            s3_results: S3 upload results with pre-signed URLs
            
        Returns:
            Page ID
        """
        # Extract chart URLs from S3 results
        chart_urls = {}
        if s3_results and "charts" in s3_results:
            for tf, chart_info in s3_results["charts"].items():
                if "url" in chart_info:
                    chart_urls[tf] = chart_info["url"]
        
        # Create the page
        page_id = self.create_page(analysis, chart_urls)
        
        return page_id