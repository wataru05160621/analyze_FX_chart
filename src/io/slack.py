"""Slack notification module."""

import json
from typing import Dict, Optional
import requests

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SlackClient:
    """Slack client for sending notifications."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Slack client."""
        self.webhook_url = webhook_url or config.slack_webhook_url
        
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured, Slack notifications disabled")
    
    def send_analysis_summary(
        self,
        analysis: Dict,
        chart_urls: Optional[Dict[str, str]] = None,
        notion_url: Optional[str] = None
    ) -> bool:
        """
        Send analysis summary to Slack.
        
        Args:
            analysis: Analysis results
            chart_urls: Optional chart URLs
            notion_url: Optional Notion page URL
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            logger.warning("Slack webhook not configured, skipping notification")
            return False
        
        # Build message
        message = self._build_message(analysis, chart_urls, notion_url)
        
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            logger.info("Sent Slack notification", run_id=analysis.get("run_id"))
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification", error=str(e))
            return False
    
    def _build_message(
        self,
        analysis: Dict,
        chart_urls: Optional[Dict[str, str]] = None,
        notion_url: Optional[str] = None
    ) -> Dict:
        """Build Slack message payload."""
        
        # Extract key fields
        pair = analysis.get("pair", "USDJPY")
        setup = analysis.get("final_setup", "No-Trade")
        confidence = analysis.get("confidence", "low")
        ev_r = analysis.get("ev_R", 0.0)
        timestamp = analysis.get("timestamp_jst", "")[:16]
        
        # Determine color based on setup
        if setup == "No-Trade":
            color = "#808080"  # Gray
        elif confidence == "high":
            color = "#00ff00"  # Green
        elif confidence == "medium":
            color = "#ffaa00"  # Orange
        else:
            color = "#ff0000"  # Red
        
        # Build main attachment
        attachment = {
            "color": color,
            "title": f"FX Analysis: {pair}",
            "title_link": notion_url if notion_url else None,
            "fields": [
                {
                    "title": "Setup",
                    "value": setup,
                    "short": True
                },
                {
                    "title": "Confidence",
                    "value": confidence,
                    "short": True
                },
                {
                    "title": "Expected Value",
                    "value": f"{ev_r:.2f}R",
                    "short": True
                },
                {
                    "title": "Time (JST)",
                    "value": timestamp,
                    "short": True
                }
            ],
            "footer": "FX Analyzer",
            "ts": int(datetime.now().timestamp())
        }
        
        # Add rationale field if available
        if "rationale" in analysis and analysis["rationale"]:
            # Take first 3 rationale items
            rationale_text = "\n".join([f"• {r}" for r in analysis["rationale"][:3]])
            attachment["fields"].append({
                "title": "Key Points",
                "value": rationale_text,
                "short": False
            })
        
        # Add trade plan if setup is not No-Trade
        if setup != "No-Trade" and "plan" in analysis:
            plan = analysis["plan"]
            plan_text = []
            
            if "entry" in plan:
                plan_text.append(f"Entry: {plan['entry']}")
            if "stop_loss" in plan:
                plan_text.append(f"SL: {plan['stop_loss']}")
            if "take_profit" in plan:
                plan_text.append(f"TP: {plan['take_profit']}")
            
            if plan_text:
                attachment["fields"].append({
                    "title": "Trade Plan",
                    "value": " | ".join(plan_text),
                    "short": False
                })
        
        # Build blocks for better formatting
        blocks = []
        
        # Header block
        header_text = f"*FX Analysis Complete: {pair}*"
        if setup != "No-Trade":
            header_text += f" - _{setup} Setup Identified_"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": header_text
            }
        })
        
        # Summary block
        summary_lines = [
            f"*Setup:* {setup}",
            f"*Confidence:* {confidence}",
            f"*Expected Value:* {ev_r:.2f}R",
            f"*Time:* {timestamp} JST"
        ]
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(summary_lines)
            }
        })
        
        # Add chart links if available
        if chart_urls:
            chart_links = []
            for tf, url in chart_urls.items():
                chart_links.append(f"<{url}|{tf} Chart>")
            
            if chart_links:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Charts:* {' | '.join(chart_links)}"
                    }
                })
        
        # Add Notion link if available
        if notion_url:
            blocks.append({
                "type": "section",
                "text": {
                "type": "mrkdwn",
                    "text": f"<{notion_url}|View Full Analysis in Notion>"
                }
            })
        
        # Divider
        blocks.append({"type": "divider"})
        
        # Build final message
        message = {
            "attachments": [attachment]
        }
        
        # Add blocks if Slack supports them
        if blocks:
            message["blocks"] = blocks
        
        return message

from datetime import datetime