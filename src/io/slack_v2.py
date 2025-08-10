"""Enhanced Slack client with template-based notifications."""

import json
import requests
from typing import Dict, Optional

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SlackClientV2:
    """Enhanced Slack client with block templates."""
    
    def __init__(self):
        """Initialize Slack client."""
        self.webhook_url = config.slack_webhook_url
        
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
        
        # Load templates
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load Slack block templates."""
        try:
            from pathlib import Path
            template_path = Path(__file__).parent.parent.parent / "quality_step_bundle_full" / "slack" / "SLACK_TEMPLATES.json"
            
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Slack templates: {e}")
            # Return default templates
            return {
                "success": {
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Analysis complete"
                        }
                    }]
                },
                "failure": {
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":warning: Analysis failed"
                        }
                    }]
                },
                "no_trade": {
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "No trade opportunity"
                        }
                    }]
                }
            }
    
    def send_analysis_notification(
        self,
        analysis: Dict,
        notion_url: Optional[str] = None,
        chart_urls: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send analysis notification using appropriate template.
        
        Args:
            analysis: Analysis result dictionary
            notion_url: Notion page URL
            chart_urls: Chart URLs (optional)
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url or self.webhook_url == "https://hooks.slack.com/services/xxx":
            logger.warning("Slack webhook not properly configured")
            return False
        
        try:
            # Determine which template to use
            if analysis.get("status") == "failed":
                payload = self._build_failure_payload(analysis)
            elif analysis.get("setup") == "No-Trade" or analysis.get("status") == "no-trade":
                payload = self._build_no_trade_payload(analysis, notion_url)
            else:
                payload = self._build_success_payload(analysis, notion_url)
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(
                    "Sent Slack notification",
                    status=analysis.get("status"),
                    setup=analysis.get("setup")
                )
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _build_success_payload(self, analysis: Dict, notion_url: Optional[str]) -> Dict:
        """Build success notification payload."""
        template = self.templates.get("success", {})
        blocks = []
        
        # Build main section
        setup = analysis.get("setup", "Unknown")
        setup_name = {
            "A": "Pattern Break",
            "B": "PB Pullback",
            "C": "Probe Reversal",
            "D": "Failed Break Rev",
            "E": "Momentum Cont",
            "F": "Range Scalp"
        }.get(setup, setup)
        
        # Create summary (max 120 chars)
        rationale = analysis.get("rationale", [])
        summary = " | ".join(rationale[:2]) if rationale else "Trade setup identified"
        if len(summary) > 120:
            summary = summary[:117] + "..."
        
        main_text = (
            f"*{analysis.get('pair', 'USDJPY')} {analysis.get('timeframe', '5m')}* "
            f"{setup_name} EV {analysis.get('ev_R', 0):.2f}R — {summary}"
        )
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": main_text
            }
        })
        
        # Build context section
        plan = analysis.get("plan", {})
        context_text = (
            f"TP {plan.get('tp_pips', 0):.1f} / SL {plan.get('sl_pips', 0):.1f}｜"
            f"Confluence {analysis.get('confluence_count', 0)}"
        )
        
        if notion_url:
            context_text += f"｜<{notion_url}|Notion>"
        
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": context_text
            }]
        })
        
        return {"blocks": blocks}
    
    def _build_failure_payload(self, analysis: Dict) -> Dict:
        """Build failure notification payload."""
        template = self.templates.get("failure", {})
        blocks = []
        
        # Determine failure phase
        phase = "Unknown"
        error_msg = "Analysis failed"
        
        if "error" in analysis:
            error_msg = str(analysis["error"])[:100]
            if "data" in error_msg.lower():
                phase = "Data Fetch"
            elif "analysis" in error_msg.lower():
                phase = "Analysis"
            elif "notion" in error_msg.lower():
                phase = "Notion Upload"
            elif "s3" in error_msg.lower():
                phase = "S3 Upload"
        
        main_text = f":warning: *失敗* {phase} — {error_msg}"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": main_text
            }
        })
        
        # Add context with retry policy
        retry_policy = "5分後に自動リトライ"
        context_text = f"再試行: {retry_policy}｜RunId {analysis.get('run_id', 'N/A')}"
        
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": context_text
            }]
        })
        
        return {"blocks": blocks}
    
    def _build_no_trade_payload(self, analysis: Dict, notion_url: Optional[str]) -> Dict:
        """Build no-trade notification payload."""
        template = self.templates.get("no_trade", {})
        blocks = []
        
        # Format no-trade reasons
        reasons = analysis.get("no_trade_reasons", [])
        if reasons:
            reasons_text = ", ".join(reasons[:3])  # Limit to 3 reasons
            if len(reasons) > 3:
                reasons_text += f" (+{len(reasons)-3} more)"
        else:
            reasons_text = "条件未達"
        
        main_text = f"*No-Trade* 理由: {reasons_text}"
        
        if notion_url:
            main_text += f" — <{notion_url}|Notion>"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": main_text
            }
        })
        
        return {"blocks": blocks}
    
    def send_daily_stats(self, stats: Dict) -> bool:
        """
        Send daily statistics summary.
        
        Args:
            stats: Daily statistics dictionary
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url or self.webhook_url == "https://hooks.slack.com/services/xxx":
            return False
        
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Daily Statistics"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Total Runs:* {stats.get('total_runs', 0)}\n"
                            f"*Setups Found:* {stats.get('setups_found', 0)}\n"
                            f"*No-Trades:* {stats.get('no_trades', 0)}\n"
                            f"*Failures:* {stats.get('failures', 0)}\n"
                            f"*Avg EV:* {stats.get('avg_ev', 0):.2f}R\n"
                            f"*Top Setup:* {stats.get('top_setup', 'N/A')}"
                        )
                    }
                }
            ]
            
            payload = {"blocks": blocks}
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send daily stats: {e}")
            return False