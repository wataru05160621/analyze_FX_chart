"""Enhanced Notion client with v2 contract support."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from notion_client import Client

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotionClientV2:
    """Enhanced Notion client with extended properties and structured content."""
    
    def __init__(self):
        """Initialize Notion client."""
        self.api_key = config.notion_api_key
        self.db_id = config.notion_db_id
        
        if not self.api_key or not self.db_id:
            raise ValueError("Notion API key and database ID required")
        
        self.client = Client(auth=self.api_key)
        self.engine_version = "v2.0.0"
        logger.info("Initialized Notion client v2", db_id=self.db_id)
    
    def create_analysis_page(
        self,
        analysis: Dict,
        chart_urls: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a Notion page with v2 contract compliance.
        
        Args:
            analysis: Analysis result dictionary
            chart_urls: Dict mapping timeframe to S3 URLs
            
        Returns:
            Created page ID
        """
        try:
            # Build page properties
            properties = self._build_properties(analysis)
            
            # Build page content blocks
            children = self._build_content_blocks(analysis, chart_urls)
            
            # Create the page
            response = self.client.pages.create(
                parent={"database_id": self.db_id},
                properties=properties,
                children=children
            )
            
            page_id = response["id"]
            page_url = response.get("url", f"https://notion.so/{page_id.replace('-', '')}")
            
            logger.info(
                "Created Notion page",
                page_id=page_id,
                url=page_url,
                setup=analysis.get("setup"),
                confluence=analysis.get("confluence_count", 0)
            )
            
            return page_id
            
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise
    
    def _build_properties(self, analysis: Dict) -> Dict:
        """Build Notion page properties from analysis."""
        setup = analysis.get("setup", "No-Trade")
        indicators = analysis.get("indicators", {})
        plan = analysis.get("plan", {})
        filters = analysis.get("filters", {})
        
        # Determine build-up quality
        build_up = indicators.get("build_up", {})
        build_up_score = sum([
            build_up.get("width_pips", 0) >= 10,
            build_up.get("bars", 0) >= 10,
            build_up.get("ema_inside", False)
        ])
        build_up_quality = "Strong" if build_up_score == 3 else "Normal" if build_up_score == 2 else "Weak"
        
        # Determine 1h trend
        env_trend = "Range"  # Default, would be passed from analysis
        
        # Build multi-select options for no-trade reasons
        no_trade_options = []
        for reason in analysis.get("no_trade_reasons", []):
            if "ATR" in reason:
                no_trade_options.append({"name": "ATR<7"})
            elif "Spread" in reason:
                no_trade_options.append({"name": "Spread>2"})
            elif "news" in reason.lower():
                no_trade_options.append({"name": "NewsWindow"})
            elif "build" in reason.lower():
                no_trade_options.append({"name": "BuildUpWeak"})
            else:
                no_trade_options.append({"name": "Other"})
        
        # Build advice flags multi-select
        advice_flag_options = [{"name": flag} for flag in analysis.get("advice_flags", [])]
        
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": f"{analysis['pair']} - {setup} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": analysis["timestamp_jst"][:10]  # YYYY-MM-DD format
                }
            },
            "Currency": {
                "multi_select": [{"name": analysis["pair"]}]
            },
            "ConfluenceCount": {
                "number": analysis.get("confluence_count", 0)
            },
            "R_multiple": {
                "number": analysis.get("r_multiple", 0.0)
            },
            "BuildUpQuality": {
                "select": {"name": build_up_quality}
            },
            "Env_1hTrend": {
                "select": {"name": env_trend}
            },
            "RunId": {
                "rich_text": [
                    {
                        "text": {
                            "content": analysis["run_id"]
                        }
                    }
                ]
            },
            "EngineVersion": {
                "rich_text": [
                    {
                        "text": {
                            "content": self.engine_version
                        }
                    }
                ]
            },
            "DataSource": {
                "rich_text": [
                    {
                        "text": {
                            "content": analysis.get("data_source", "twelvedata")
                        }
                    }
                ]
            }
        }
        
        # Add Session property if SESSION environment variable is set
        session = os.environ.get('SESSION', '')
        if session:
            # Map session values to Notion select options
            session_map = {
                'tokyo_preopen': 'TokyoPre',
                'london_preopen': 'LondonPre'
            }
            properties["Session"] = {
                "select": {"name": session_map.get(session, session)}
            }
        
        # Add optional properties
        if no_trade_options:
            properties["NoTradeReason"] = {"multi_select": no_trade_options}
        
        if advice_flag_options:
            properties["AdviceFlags"] = {"multi_select": advice_flag_options}
        
        if plan:
            properties["EntryType"] = {
                "rich_text": [{"text": {"content": plan.get("entry", "")}}]
            }
            properties["TP_pips"] = {"number": plan.get("tp_pips", 0)}
            properties["SL_pips"] = {"number": plan.get("sl_pips", 0)}
        
        if analysis.get("risk"):
            properties["R_multiple"] = {"number": analysis["risk"].get("r_multiple", 0)}
        
        return properties
    
    def _build_content_blocks(self, analysis: Dict, chart_urls: Optional[Dict[str, str]]) -> List[Dict]:
        """Build Notion page content blocks following v2 template."""
        blocks = []
        
        # 1. Heading
        setup = analysis.get("setup", "No-Trade")
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": f"{analysis['pair']} {analysis['timeframe']} — Setup {setup}"
                    }
                }]
            }
        })
        
        # 2. Environment Section (1h)
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "📊 環境認識 (1h)"}
                }]
            }
        })
        
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": f"1時間足の環境: トレンド方向と強度を分析"
                    }
                }]
            }
        })
        
        # 3. Setup Rationale Section (5m)
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "🎯 セットアップ根拠 (5m)"}
                }]
            }
        })
        
        # Add rationale as bullet points
        if analysis.get("rationale"):
            rationale_items = []
            for reason in analysis["rationale"]:
                rationale_items.append({
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": reason}
                    }]
                })
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": rationale_items[0] if rationale_items else {"rich_text": []}
            })
            
            for item in rationale_items[1:]:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": item
                })
        
        # 4. Trading Plan Section
        if analysis.get("plan") and setup != "No-Trade":
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "📋 計画"}
                    }]
                }
            })
            
            plan = analysis["plan"]
            plan_text = (
                f"Entry: {plan.get('entry', 'N/A')}\n"
                f"TP: {plan.get('tp_pips', 0):.1f} pips\n"
                f"SL: {plan.get('sl_pips', 0):.1f} pips\n"
                f"Timeout: {plan.get('timeout_min', 0)} minutes\n"
                f"EV: {analysis.get('ev_R', 0):.2f}R"
            )
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": plan_text}
                    }]
                }
            })
        
        # 5. Implications Section
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "💡 示唆"}
                }]
            }
        })
        
        if analysis.get("no_trade_reasons"):
            implications = "No-Trade理由: " + ", ".join(analysis["no_trade_reasons"])
        else:
            implications = f"Confluence: {analysis.get('confluence_count', 0)} | "
            if analysis.get("advice_flags"):
                implications += "注意: 言語フィルタ適用済み"
            else:
                implications += "標準的なセットアップ条件を満たしています"
        
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": implications}
                }]
            }
        })
        
        # 6. Add Charts (5m and 1h) - MANDATORY 2 images
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "📈 チャート"}
                }]
            }
        })
        
        # Add 5m chart (mandatory)
        chart_5m_url = chart_urls.get("5m") if chart_urls else None
        if not chart_5m_url:
            # Use placeholder if no chart available
            chart_5m_url = "https://via.placeholder.com/1200x600/1a1a1a/808080?text=5m+Chart+Not+Available"
        
        blocks.append({
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": chart_5m_url
                },
                "caption": [{
                    "type": "text",
                    "text": {"content": "5分足チャート"}
                }]
            }
        })
        
        # Add 1h chart (mandatory)
        chart_1h_url = chart_urls.get("1h") if chart_urls else None
        if not chart_1h_url:
            # Use placeholder if no chart available
            chart_1h_url = "https://via.placeholder.com/1200x600/1a1a1a/808080?text=1h+Chart+Not+Available"
        
        blocks.append({
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": chart_1h_url
                },
                "caption": [{
                    "type": "text",
                    "text": {"content": "1時間足チャート"}
                }]
            }
        })
        
        # 7. Features JSON Block (IMPORTANT: Required by v2 contract)
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "🔧 Features (JSON)"}
                }]
            }
        })
        
        # Create features dictionary
        features = {
            "run_id": analysis["run_id"],
            "timestamp": analysis["timestamp_jst"],
            "indicators": analysis.get("indicators", {}),
            "filters": analysis.get("filters", {}),
            "confluence_count": analysis.get("confluence_count", 0),
            "ev_R": analysis.get("ev_R", 0),
            "setup": analysis.get("setup", "No-Trade"),
            "rationale": analysis.get("rationale", []),
            "no_trade_reasons": analysis.get("no_trade_reasons", []),
            "advice_flags": analysis.get("advice_flags", [])
        }
        
        # Add as code block
        blocks.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": json.dumps(features, indent=2, ensure_ascii=False)
                    }
                }],
                "language": "json",
                "caption": []
            }
        })
        
        return blocks