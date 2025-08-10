"""Daily statistics job for trade result evaluation and stats calculation."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
import pandas as pd
from notion_client import Client

from src.utils.config import config
from src.utils.logger import get_logger
from src.data_fetcher.twelvedata import TwelveDataClient
from src.io.s3 import S3Client
from src.io.slack_v2 import SlackClientV2

logger = get_logger(__name__)


class DailyStatsJob:
    """Daily statistics job that runs at 23:45 JST."""
    
    def __init__(self):
        """Initialize the daily stats job."""
        self.jst = pytz.timezone("Asia/Tokyo")
        self.notion_client = Client(auth=config.notion_api_key)
        self.twelve_data = TwelveDataClient()
        self.s3_client = S3Client()
        self.slack_client = SlackClientV2()
        
        # Load existing stats
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """Load existing statistics from S3."""
        try:
            # Try to download existing stats
            stats_key = "stats/setup_stats.json"
            stats_data = self.s3_client.client.get_object(
                Bucket=self.s3_client.bucket,
                Key=stats_key
            )
            
            existing_stats = json.loads(stats_data['Body'].read())
            logger.info("Loaded existing stats from S3")
            return existing_stats
            
        except Exception as e:
            logger.info(f"No existing stats found, starting fresh: {e}")
            # Initialize with default values
            return {
                "last_updated": None,
                "setups": {
                    "A": {"alpha": 3, "beta": 2, "wins": 0, "losses": 0, "p_ewma": 0.6},
                    "B": {"alpha": 2.5, "beta": 2, "wins": 0, "losses": 0, "p_ewma": 0.55},
                    "C": {"alpha": 2, "beta": 3, "wins": 0, "losses": 0, "p_ewma": 0.4},
                    "D": {"alpha": 2, "beta": 3, "wins": 0, "losses": 0, "p_ewma": 0.4},
                    "E": {"alpha": 3.5, "beta": 1.5, "wins": 0, "losses": 0, "p_ewma": 0.7},
                    "F": {"alpha": 1.5, "beta": 3, "wins": 0, "losses": 0, "p_ewma": 0.33}
                },
                "daily_summaries": []
            }
    
    def run(self) -> Dict:
        """
        Execute the daily stats job.
        
        Returns:
            Statistics summary
        """
        logger.info("Starting daily stats job")
        
        today = datetime.now(self.jst).date()
        start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=self.jst)
        
        # Step 1: Query today's Notion pages
        pages = self._query_todays_pages(start_of_day)
        logger.info(f"Found {len(pages)} pages for today")
        
        # Step 2: Process each page
        results = []
        for page in pages:
            try:
                result = self._process_page(page)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to process page: {e}")
        
        # Step 3: Update statistics
        self._update_statistics(results)
        
        # Step 4: Save to S3
        self._save_stats()
        
        # Step 5: Send summary to Slack
        summary = self._create_summary(results)
        self.slack_client.send_daily_stats(summary)
        
        logger.info(
            "Daily stats job completed",
            processed=len(results),
            wins=sum(1 for r in results if r["result"] == "TP"),
            losses=sum(1 for r in results if r["result"] == "SL")
        )
        
        return summary
    
    def _query_todays_pages(self, start_date: datetime) -> List[Dict]:
        """Query Notion for today's pages."""
        try:
            # Query the database
            response = self.notion_client.databases.query(
                database_id=config.notion_db_id,
                filter={
                    "and": [
                        {
                            "property": "Date",
                            "date": {
                                "on_or_after": start_date.isoformat()
                            }
                        },
                        {
                            "property": "Setup",
                            "select": {
                                "does_not_equal": "No-Trade"
                            }
                        }
                    ]
                }
            )
            
            return response.get("results", [])
            
        except Exception as e:
            logger.error(f"Failed to query Notion: {e}")
            return []
    
    def _process_page(self, page: Dict) -> Optional[Dict]:
        """
        Process a single Notion page to determine trade result.
        
        Args:
            page: Notion page object
            
        Returns:
            Result dictionary or None
        """
        try:
            properties = page.get("properties", {})
            
            # Extract required fields
            run_id = self._get_text_property(properties.get("RunId"))
            setup = self._get_select_property(properties.get("Setup"))
            auto_result = self._get_select_property(properties.get("AutoResult"))
            
            # Skip if already processed
            if auto_result:
                logger.info(f"Page already processed: {run_id}")
                return None
            
            # Get trade parameters
            tp_pips = self._get_number_property(properties.get("TP_pips"))
            sl_pips = self._get_number_property(properties.get("SL_pips"))
            entry_type = self._get_text_property(properties.get("EntryType"))
            
            if not all([tp_pips, sl_pips, entry_type]):
                logger.warning(f"Missing trade parameters for {run_id}")
                return None
            
            # Get entry time (assume it's the page creation time)
            created_time = datetime.fromisoformat(page["created_time"].replace("Z", "+00:00"))
            entry_time = created_time.astimezone(self.jst)
            
            # Fetch price data after entry
            result = self._evaluate_trade(
                entry_time,
                entry_type,
                tp_pips,
                sl_pips
            )
            
            # Update the Notion page
            self._update_page(page["id"], result)
            
            return {
                "run_id": run_id,
                "setup": setup,
                "result": result["auto_result"],
                "pnl_pips": result["pnl_pips"],
                "r_multiple": result["r_multiple"]
            }
            
        except Exception as e:
            logger.error(f"Failed to process page: {e}")
            return None
    
    def _evaluate_trade(
        self,
        entry_time: datetime,
        entry_type: str,
        tp_pips: float,
        sl_pips: float
    ) -> Dict:
        """
        Evaluate trade outcome based on subsequent price data.
        
        Args:
            entry_time: Entry timestamp
            entry_type: Entry signal type
            tp_pips: Take profit in pips
            sl_pips: Stop loss in pips
            
        Returns:
            Trade result dictionary
        """
        # Fetch 5-minute data for the next 90 minutes
        end_time = entry_time + timedelta(minutes=90)
        
        try:
            # Fetch data
            df = self.twelve_data.fetch_time_series(
                symbol="USD/JPY",
                interval="5min",
                outputsize=20  # 20 bars = 100 minutes
            )
            
            # Filter to after entry time
            df_after = df[df.index > entry_time]
            
            if df_after.empty:
                return {
                    "auto_result": "NoFill",
                    "pnl_pips": 0,
                    "r_multiple": 0
                }
            
            # Get entry price (close of entry bar)
            entry_price = df[df.index <= entry_time].iloc[-1]["close"]
            
            # Determine direction (simplified - would parse from entry_type)
            is_long = "buy" in entry_type.lower() or "long" in entry_type.lower()
            
            # Calculate TP/SL levels
            if is_long:
                tp_price = entry_price + (tp_pips / 100)  # Convert pips to price for JPY
                sl_price = entry_price - (sl_pips / 100)
            else:
                tp_price = entry_price - (tp_pips / 100)
                sl_price = entry_price + (sl_pips / 100)
            
            # Check each bar
            for idx, row in df_after.iterrows():
                # Check if timeout
                if idx > end_time:
                    return {
                        "auto_result": "Timeout",
                        "pnl_pips": 0,
                        "r_multiple": 0
                    }
                
                # Check TP/SL hit
                if is_long:
                    if row["high"] >= tp_price:
                        # TP hit
                        return {
                            "auto_result": "TP",
                            "pnl_pips": tp_pips,
                            "r_multiple": tp_pips / sl_pips
                        }
                    elif row["low"] <= sl_price:
                        # SL hit
                        return {
                            "auto_result": "SL",
                            "pnl_pips": -sl_pips,
                            "r_multiple": -1
                        }
                else:
                    if row["low"] <= tp_price:
                        # TP hit
                        return {
                            "auto_result": "TP",
                            "pnl_pips": tp_pips,
                            "r_multiple": tp_pips / sl_pips
                        }
                    elif row["high"] >= sl_price:
                        # SL hit
                        return {
                            "auto_result": "SL",
                            "pnl_pips": -sl_pips,
                            "r_multiple": -1
                        }
            
            # Timeout if no hit within data
            return {
                "auto_result": "Timeout",
                "pnl_pips": 0,
                "r_multiple": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate trade: {e}")
            return {
                "auto_result": "NoFill",
                "pnl_pips": 0,
                "r_multiple": 0
            }
    
    def _update_page(self, page_id: str, result: Dict):
        """Update Notion page with trade result."""
        try:
            self.notion_client.pages.update(
                page_id=page_id,
                properties={
                    "AutoResult": {
                        "select": {"name": result["auto_result"]}
                    },
                    "PnL_pips": {
                        "number": result["pnl_pips"]
                    },
                    "R_multiple": {
                        "number": result["r_multiple"]
                    }
                }
            )
            logger.info(f"Updated page {page_id} with result: {result['auto_result']}")
            
        except Exception as e:
            logger.error(f"Failed to update page: {e}")
    
    def _update_statistics(self, results: List[Dict]):
        """Update setup statistics with Beta + EWMA."""
        for result in results:
            setup = result["setup"]
            if setup not in self.stats["setups"]:
                continue
            
            setup_stats = self.stats["setups"][setup]
            
            # Update win/loss counts
            if result["result"] == "TP":
                setup_stats["wins"] += 1
                setup_stats["alpha"] += 0.1  # Slight increase for win
            elif result["result"] == "SL":
                setup_stats["losses"] += 1
                setup_stats["beta"] += 0.1  # Slight increase for loss
            
            # Calculate new win rate from Beta distribution
            alpha = setup_stats["alpha"]
            beta = setup_stats["beta"]
            p_beta = alpha / (alpha + beta)
            
            # Apply EWMA (exponentially weighted moving average)
            lambda_ewma = 0.9  # Decay factor
            p_old = setup_stats["p_ewma"]
            p_new = lambda_ewma * p_beta + (1 - lambda_ewma) * p_old
            
            setup_stats["p_ewma"] = round(p_new, 4)
        
        # Update timestamp
        self.stats["last_updated"] = datetime.now(self.jst).isoformat()
    
    def _save_stats(self):
        """Save statistics to S3."""
        try:
            stats_key = "stats/setup_stats.json"
            stats_json = json.dumps(self.stats, indent=2, ensure_ascii=False)
            
            self.s3_client.client.put_object(
                Bucket=self.s3_client.bucket,
                Key=stats_key,
                Body=stats_json.encode('utf-8'),
                ContentType='application/json'
            )
            
            logger.info(f"Saved stats to S3: {stats_key}")
            
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def _create_summary(self, results: List[Dict]) -> Dict:
        """Create daily summary."""
        total_pnl = sum(r["pnl_pips"] for r in results)
        wins = [r for r in results if r["result"] == "TP"]
        losses = [r for r in results if r["result"] == "SL"]
        
        # Count by setup
        setup_counts = {}
        for r in results:
            setup = r["setup"]
            if setup not in setup_counts:
                setup_counts[setup] = {"total": 0, "wins": 0}
            setup_counts[setup]["total"] += 1
            if r["result"] == "TP":
                setup_counts[setup]["wins"] += 1
        
        # Find top setup
        top_setup = None
        if setup_counts:
            top_setup = max(setup_counts.items(), 
                          key=lambda x: x[1]["wins"] / x[1]["total"] if x[1]["total"] > 0 else 0)[0]
        
        return {
            "date": datetime.now(self.jst).date().isoformat(),
            "total_runs": len(results),
            "setups_found": len([r for r in results if r["setup"] != "No-Trade"]),
            "no_trades": 0,  # All processed are trades
            "failures": 0,
            "wins": len(wins),
            "losses": len(losses),
            "total_pnl_pips": round(total_pnl, 1),
            "avg_ev": round(sum(r["r_multiple"] for r in results) / len(results), 2) if results else 0,
            "top_setup": top_setup,
            "setup_performance": setup_counts
        }
    
    def _get_text_property(self, prop: Optional[Dict]) -> Optional[str]:
        """Extract text from Notion property."""
        if not prop:
            return None
        
        if "rich_text" in prop:
            texts = prop["rich_text"]
            if texts and len(texts) > 0:
                return texts[0]["text"]["content"]
        elif "title" in prop:
            texts = prop["title"]
            if texts and len(texts) > 0:
                return texts[0]["text"]["content"]
        
        return None
    
    def _get_select_property(self, prop: Optional[Dict]) -> Optional[str]:
        """Extract select value from Notion property."""
        if not prop or "select" not in prop:
            return None
        
        select = prop["select"]
        if select:
            return select.get("name")
        
        return None
    
    def _get_number_property(self, prop: Optional[Dict]) -> Optional[float]:
        """Extract number from Notion property."""
        if not prop or "number" not in prop:
            return None
        
        return prop["number"]


def main():
    """Main entry point for daily stats job."""
    logger.info("Daily stats job starting")
    
    try:
        job = DailyStatsJob()
        summary = job.run()
        
        # Save summary to file
        with open("daily_stats_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info("Daily stats job completed successfully")
        
    except Exception as e:
        logger.error(f"Daily stats job failed: {e}")
        raise


if __name__ == "__main__":
    main()