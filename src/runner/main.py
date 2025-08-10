"""Main runner for FX analysis system."""

import sys
import traceback
from typing import Dict, Optional

from src.utils.config import config
from src.utils.logger import get_logger
from src.data_fetcher.twelvedata import fetch_multi_timeframe_data
from src.analysis.core import FXAnalyzer
from src.charting.mpl import ChartGenerator
from src.io.s3 import S3Client
from src.io.notion import NotionClient
from src.io.slack import SlackClient

logger = get_logger(__name__)

class FXAnalysisRunner:
    """Main orchestrator for FX analysis workflow."""
    
    def __init__(self):
        """Initialize the runner."""
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
        
        # Initialize components
        self.analyzer = FXAnalyzer()
        self.chart_generator = ChartGenerator()
        self.s3_client = None
        self.notion_client = None
        self.slack_client = None
        
        # Initialize clients with error handling
        try:
            self.s3_client = S3Client()
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {e}")
        
        try:
            self.notion_client = NotionClient()
        except Exception as e:
            logger.warning(f"Notion client initialization failed: {e}")
        
        try:
            self.slack_client = SlackClient()
        except Exception as e:
            logger.warning(f"Slack client initialization failed: {e}")
    
    def run(self) -> Dict:
        """
        Execute the complete analysis workflow.
        
        Returns:
            Dict with analysis results and status
        """
        logger.info("Starting FX analysis run", pair=config.pair, timeframes=config.timeframes)
        
        results = {
            "status": "started",
            "errors": []
        }
        
        try:
            # Step 1: Fetch data
            logger.info("Fetching market data")
            data = fetch_multi_timeframe_data()
            
            if not data:
                raise ValueError("No data fetched from TwelveData")
            
            # Step 2: Analyze data
            logger.info("Analyzing market data")
            analysis = self.analyzer.analyze(data)
            results["analysis"] = analysis
            
            # Step 3: Generate charts
            logger.info("Generating charts")
            charts = self.chart_generator.generate_multi_timeframe_charts(data, analysis)
            
            # Step 4: Upload to S3
            s3_results = None
            if self.s3_client and charts:
                try:
                    logger.info("Uploading to S3")
                    s3_results = self.s3_client.upload_analysis_artifacts(analysis, charts)
                    results["s3"] = s3_results
                except Exception as e:
                    logger.error(f"S3 upload failed: {e}")
                    results["errors"].append(f"S3: {str(e)}")
            
            # Step 5: Create Notion page
            notion_page_id = None
            notion_url = None
            if self.notion_client:
                try:
                    logger.info("Creating Notion page")
                    notion_page_id = self.notion_client.update_analysis_result(analysis, s3_results)
                    results["notion_page_id"] = notion_page_id
                    # Generate Notion URL (approximation)
                    notion_url = f"https://notion.so/{notion_page_id.replace('-', '')}"
                except Exception as e:
                    logger.error(f"Notion update failed: {e}")
                    results["errors"].append(f"Notion: {str(e)}")
            
            # Step 6: Send Slack notification
            if self.slack_client:
                try:
                    logger.info("Sending Slack notification")
                    # Extract chart URLs from S3 results
                    chart_urls = {}
                    if s3_results and "charts" in s3_results:
                        for tf, info in s3_results["charts"].items():
                            if "url" in info:
                                chart_urls[tf] = info["url"]
                    
                    slack_sent = self.slack_client.send_analysis_summary(
                        analysis,
                        chart_urls=chart_urls,
                        notion_url=notion_url
                    )
                    results["slack_sent"] = slack_sent
                except Exception as e:
                    logger.error(f"Slack notification failed: {e}")
                    results["errors"].append(f"Slack: {str(e)}")
            
            # Update status
            if results["errors"]:
                results["status"] = "completed_with_errors"
            else:
                results["status"] = "completed"
            
            logger.info(
                "Analysis run completed",
                status=results["status"],
                run_id=analysis.get("run_id"),
                setup=analysis.get("final_setup"),
                errors_count=len(results["errors"])
            )
            
        except Exception as e:
            logger.error(f"Analysis run failed: {e}")
            logger.error(traceback.format_exc())
            results["status"] = "failed"
            results["errors"].append(str(e))
        
        return results

def main():
    """Main entry point."""
    logger.info("FX Analysis System starting")
    
    try:
        runner = FXAnalysisRunner()
        results = runner.run()
        
        # Exit with appropriate code
        if results["status"] == "failed":
            sys.exit(1)
        elif results["status"] == "completed_with_errors":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()