"""Enhanced main runner with v2 quality improvements."""

import sys
import json
import traceback
from typing import Dict, Optional
from pathlib import Path

from src.utils.config import config
from src.utils.logger import get_logger
from src.data_fetcher.twelvedata import fetch_multi_timeframe_data
from src.analysis.core_v2 import FXAnalyzerV2
from src.charting.mpl import ChartGenerator
from src.io.s3 import S3Client
from src.io.notion_v2 import NotionClientV2
from src.io.slack_v2 import SlackClientV2

logger = get_logger(__name__)


class FXAnalysisRunnerV2:
    """Enhanced main orchestrator with schema compliance and quality gates."""
    
    def __init__(self):
        """Initialize the enhanced runner."""
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
        
        # Initialize components
        self.analyzer = FXAnalyzerV2(pair=config.pair)
        self.chart_generator = ChartGenerator(pair=config.pair)
        self.s3_client = None
        self.notion_client = None
        self.slack_client = None
        
        # Initialize clients with error handling
        try:
            self.s3_client = S3Client()
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {e}")
        
        try:
            self.notion_client = NotionClientV2()
        except Exception as e:
            logger.warning(f"Notion client initialization failed: {e}")
        
        try:
            self.slack_client = SlackClientV2()
        except Exception as e:
            logger.warning(f"Slack client initialization failed: {e}")
    
    def run(self) -> Dict:
        """
        Execute the complete analysis workflow with v2 enhancements.
        
        Returns:
            Schema-compliant analysis result
        """
        logger.info("Starting FX analysis run v2", pair=config.pair, timeframes=config.timeframes)
        
        analysis = None
        
        try:
            # Step 1: Fetch data
            logger.info("Fetching market data")
            data = fetch_multi_timeframe_data()
            
            if not data:
                raise ValueError("No data fetched from TwelveData")
            
            # Step 2: Analyze data with v2 analyzer
            logger.info("Analyzing market data with v2 engine")
            analysis = self.analyzer.analyze(data)
            
            # Step 3: Generate charts
            logger.info("Generating charts")
            charts = self.chart_generator.generate_multi_timeframe_charts(data, analysis)
            
            # Step 4: Upload to S3
            chart_urls = {}
            s3_results = None
            if self.s3_client and charts:
                try:
                    logger.info("Uploading to S3")
                    s3_results = self.s3_client.upload_analysis_artifacts(analysis, charts)
                    
                    # Extract chart URLs
                    if s3_results and "charts" in s3_results:
                        for tf, info in s3_results["charts"].items():
                            if "url" in info:
                                chart_urls[tf] = info["url"]
                    
                    # Add chart information to analysis
                    analysis["charts"] = [
                        {
                            "timeframe": tf,
                            "s3_key": info.get("key", ""),
                            "s3_presigned_url": info.get("url", ""),
                            "width_px": 1200,
                            "height_px": 600
                        }
                        for tf, info in s3_results.get("charts", {}).items()
                    ]
                    
                except Exception as e:
                    logger.error(f"S3 upload failed: {e}")
                    analysis["status"] = "failed"
                    analysis["error"] = f"S3: {str(e)}"
            
            # Step 5: Validate against schema
            if not self._validate_schema(analysis):
                logger.warning("Analysis does not fully comply with schema")
            
            # Step 6: Create Notion page
            notion_page_id = None
            notion_url = None
            if self.notion_client and analysis["status"] != "failed":
                try:
                    logger.info("Creating Notion page with v2 client")
                    
                    # Extract chart URLs for Notion
                    chart_urls = {}
                    if s3_results and "charts" in s3_results:
                        for tf, info in s3_results["charts"].items():
                            if "url" in info:
                                chart_urls[tf] = info["url"]
                    
                    notion_page_id = self.notion_client.create_analysis_page(analysis, chart_urls)
                    
                    # Generate Notion URL
                    notion_url = f"https://notion.so/{notion_page_id.replace('-', '')}"
                    
                except Exception as e:
                    logger.error(f"Notion update failed: {e}")
                    analysis["status"] = "failed"
                    analysis["error"] = f"Notion: {str(e)}"
            
            # Step 7: Send Slack notification
            if self.slack_client:
                try:
                    logger.info("Sending Slack notification with v2 template")
                    self.slack_client.send_analysis_notification(
                        analysis,
                        notion_url=notion_url,
                        chart_urls=chart_urls
                    )
                    
                except Exception as e:
                    logger.error(f"Slack notification failed: {e}")
                    # Don't mark as failed for Slack errors
            
            # Log completion
            logger.info(
                "Analysis run completed",
                status=analysis["status"],
                run_id=analysis["run_id"],
                setup=analysis["setup"],
                confluence=analysis["confluence_count"],
                ev_R=analysis["ev_R"],
                advice_flags=len(analysis.get("advice_flags", []))
            )
            
        except Exception as e:
            logger.error(f"Analysis run failed: {e}")
            logger.error(traceback.format_exc())
            
            # Create failure analysis object
            if not analysis:
                analysis = {
                    "run_id": "failed",
                    "status": "failed",
                    "error": str(e)
                }
            else:
                analysis["status"] = "failed"
                analysis["error"] = str(e)
            
            # Send failure notification
            if self.slack_client:
                try:
                    self.slack_client.send_analysis_notification(analysis)
                except:
                    pass
        
        return analysis
    
    def _validate_schema(self, analysis: Dict) -> bool:
        """
        Validate analysis against schema.
        
        Args:
            analysis: Analysis result to validate
            
        Returns:
            True if valid
        """
        try:
            # Load schema
            schema_path = Path(__file__).parent.parent.parent / "quality_step_bundle_full" / "schema" / "analysis_output.schema.json"
            
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in analysis:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Basic type checks
            if not isinstance(analysis.get("rationale", []), list):
                logger.warning("Rationale must be a list")
                return False
            
            if len(analysis.get("rationale", [])) < 3 and analysis.get("setup") != "No-Trade":
                logger.warning("Rationale must have at least 3 items for trade setups")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False


def main():
    """Main entry point for v2 runner."""
    logger.info("FX Analysis System v2 starting")
    
    try:
        runner = FXAnalysisRunnerV2()
        results = runner.run()
        
        # Save results to file for debugging (only in local environment)
        try:
            with open("/tmp/analysis_result.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        except:
            pass  # Ignore file write errors in container
        
        # Exit with appropriate code
        if results.get("status") == "failed":
            sys.exit(1)
        elif results.get("status") == "no-trade":
            sys.exit(0)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()