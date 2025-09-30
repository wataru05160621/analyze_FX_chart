#!/usr/bin/env python
"""
Analysis script to identify why all trades are being filtered out.

This script analyzes Notion database entries from the past 3 weeks to:
1. Identify which filters are triggering most frequently
2. Calculate statistics on each filter's trigger rate
3. Identify time-based patterns
4. Generate recommendations for filter adjustments
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import pytz

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from notion_client import Client
from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotionFilterAnalyzer:
    """Analyzer for Notion database entries to identify filter patterns."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.jst = pytz.timezone("Asia/Tokyo")
        self.notion_client = Client(auth=config.notion_api_key)
        
        # Filter thresholds from core_v2.py
        self.filter_thresholds = {
            "atr_min": 7.0,
            "spread_max": 2.0,
            "buildup_min_width": 10.0,
            "buildup_min_bars": 10,
            "news_window_hours": [9, 15, 22]  # JST
        }
        
    def fetch_recent_entries(self, weeks_back: int = 3) -> List[Dict]:
        """
        Fetch entries from the past N weeks from Notion database.
        
        Args:
            weeks_back: Number of weeks to look back
            
        Returns:
            List of Notion page objects
        """
        # Calculate date range
        end_date = datetime.now(self.jst)
        start_date = end_date - timedelta(weeks=weeks_back)
        
        logger.info(f"Fetching entries from {start_date.date()} to {end_date.date()}")
        
        try:
            all_results = []
            has_more = True
            next_cursor = None
            
            while has_more:
                # Build query
                query = {
                    "database_id": config.notion_db_id,
                    "filter": {
                        "property": "Date",
                        "date": {
                            "on_or_after": start_date.isoformat()
                        }
                    },
                    "sorts": [
                        {
                            "property": "Date",
                            "direction": "descending"
                        }
                    ]
                }
                
                if next_cursor:
                    query["start_cursor"] = next_cursor
                
                response = self.notion_client.databases.query(**query)
                
                all_results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")
                
                logger.info(f"Fetched {len(response.get('results', []))} entries...")
            
            logger.info(f"Total entries fetched: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"Failed to fetch Notion entries: {e}")
            return []
    
    def extract_entry_data(self, pages: List[Dict]) -> pd.DataFrame:
        """
        Extract relevant data from Notion pages into a DataFrame.
        
        Args:
            pages: List of Notion page objects
            
        Returns:
            DataFrame with extracted data
        """
        entries = []
        
        for page in pages:
            try:
                properties = page.get("properties", {})
                
                # Extract data
                entry = {
                    "page_id": page.get("id", ""),
                    "created_time": page.get("created_time", ""),
                    "run_id": self._get_text_property(properties.get("RunId")),
                    "date": self._get_date_property(properties.get("Date")),
                    "currency": self._get_text_property(properties.get("Currency")),
                    "timeframe": self._get_text_property(properties.get("Timeframe")),
                    "setup": self._get_select_property(properties.get("Setup")),
                    "confidence": self._get_select_property(properties.get("Confidence")),
                    "status": self._get_select_property(properties.get("Status")),
                    "ev_r": self._get_number_property(properties.get("EV_R")),
                    "entry_type": self._get_text_property(properties.get("EntryType")),
                    "tp_pips": self._get_number_property(properties.get("TP_pips")),
                    "sl_pips": self._get_number_property(properties.get("SL_pips")),
                    "summary": self._get_text_property(properties.get("Summary")),
                    # Analysis specific fields (if available)
                    "atr": self._extract_from_summary(properties.get("Summary"), "ATR"),
                    "spread": self._extract_from_summary(properties.get("Summary"), "Spread"),
                    "buildup_width": self._extract_from_summary(properties.get("Summary"), "width"),
                    "buildup_bars": self._extract_from_summary(properties.get("Summary"), "bars"),
                }
                
                # Parse created time to JST
                if entry["created_time"]:
                    created_dt = datetime.fromisoformat(entry["created_time"].replace("Z", "+00:00"))
                    entry["created_time_jst"] = created_dt.astimezone(self.jst)
                    entry["hour_jst"] = entry["created_time_jst"].hour
                else:
                    entry["created_time_jst"] = None
                    entry["hour_jst"] = None
                
                entries.append(entry)
                
            except Exception as e:
                logger.warning(f"Failed to extract data from page: {e}")
                continue
        
        df = pd.DataFrame(entries)
        logger.info(f"Extracted data from {len(df)} entries")
        
        return df
    
    def analyze_filter_triggers(self, df: pd.DataFrame) -> Dict:
        """
        Analyze which filters are triggering and their frequency.
        
        Args:
            df: DataFrame with entry data
            
        Returns:
            Analysis results dictionary
        """
        analysis = {
            "total_entries": len(df),
            "no_trade_entries": len(df[df["setup"] == "No-Trade"]),
            "trade_entries": len(df[df["setup"] != "No-Trade"]),
            "filter_triggers": {},
            "time_patterns": {},
            "setup_distribution": {},
            "recommendations": []
        }
        
        # Calculate filter trigger rates
        no_trade_df = df[df["setup"] == "No-Trade"]
        
        if len(no_trade_df) > 0:
            # ATR Filter Analysis
            atr_violations = 0
            atr_values = []
            for _, row in no_trade_df.iterrows():
                summary = row["summary"] or ""
                if "ATR too low" in summary:
                    atr_violations += 1
                # Extract ATR values
                atr_val = self._extract_numeric_from_text(summary, "ATR.*?([0-9.]+)p")
                if atr_val:
                    atr_values.append(atr_val)
            
            # Spread Filter Analysis
            spread_violations = 0
            spread_values = []
            for _, row in no_trade_df.iterrows():
                summary = row["summary"] or ""
                if "Spread too wide" in summary:
                    spread_violations += 1
                # Extract spread values
                spread_val = self._extract_numeric_from_text(summary, "Spread.*?([0-9.]+)p")
                if spread_val:
                    spread_values.append(spread_val)
            
            # News Window Analysis
            news_violations = 0
            for _, row in no_trade_df.iterrows():
                summary = row["summary"] or ""
                if "news window" in summary.lower() or "session open" in summary.lower():
                    news_violations += 1
            
            # Build-up Analysis
            buildup_violations = 0
            buildup_widths = []
            buildup_bars_list = []
            for _, row in no_trade_df.iterrows():
                summary = row["summary"] or ""
                if "build-up" in summary.lower() and ("insufficient" in summary.lower() or "quality" in summary.lower()):
                    buildup_violations += 1
                # Extract build-up metrics
                width_val = self._extract_numeric_from_text(summary, "([0-9.]+)p.*?x.*?[0-9]+ bars")
                if width_val:
                    buildup_widths.append(width_val)
                bars_val = self._extract_numeric_from_text(summary, "[0-9.]+p.*?x.*?([0-9]+) bars")
                if bars_val:
                    buildup_bars_list.append(bars_val)
            
            # Store filter analysis
            analysis["filter_triggers"] = {
                "atr_violations": {
                    "count": atr_violations,
                    "percentage": round(atr_violations / len(no_trade_df) * 100, 1),
                    "avg_value": round(sum(atr_values) / len(atr_values), 2) if atr_values else None,
                    "threshold": self.filter_thresholds["atr_min"]
                },
                "spread_violations": {
                    "count": spread_violations,
                    "percentage": round(spread_violations / len(no_trade_df) * 100, 1),
                    "avg_value": round(sum(spread_values) / len(spread_values), 2) if spread_values else None,
                    "threshold": self.filter_thresholds["spread_max"]
                },
                "news_window_violations": {
                    "count": news_violations,
                    "percentage": round(news_violations / len(no_trade_df) * 100, 1),
                    "threshold_hours": self.filter_thresholds["news_window_hours"]
                },
                "buildup_violations": {
                    "count": buildup_violations,
                    "percentage": round(buildup_violations / len(no_trade_df) * 100, 1),
                    "avg_width": round(sum(buildup_widths) / len(buildup_widths), 2) if buildup_widths else None,
                    "avg_bars": round(sum(buildup_bars_list) / len(buildup_bars_list), 2) if buildup_bars_list else None,
                    "min_width_threshold": self.filter_thresholds["buildup_min_width"],
                    "min_bars_threshold": self.filter_thresholds["buildup_min_bars"]
                }
            }
        
        # Time-based patterns
        if len(df) > 0:
            hourly_distribution = df.groupby("hour_jst").size().to_dict()
            no_trade_hourly = no_trade_df.groupby("hour_jst").size().to_dict()
            
            analysis["time_patterns"] = {
                "hourly_distribution": hourly_distribution,
                "no_trade_hourly": no_trade_hourly,
                "peak_no_trade_hours": sorted(no_trade_hourly.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        # Setup distribution
        setup_counts = df["setup"].value_counts().to_dict()
        analysis["setup_distribution"] = setup_counts
        
        return analysis
    
    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """
        Generate recommendations based on filter analysis.
        
        Args:
            analysis: Analysis results
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        filter_triggers = analysis["filter_triggers"]
        
        # ATR recommendations
        atr_data = filter_triggers.get("atr_violations", {})
        if atr_data.get("percentage", 0) > 30:
            avg_atr = atr_data.get("avg_value", 0)
            if avg_atr > 0:
                new_threshold = max(3, avg_atr * 0.8)  # Reduce by 20% but keep minimum of 3
                recommendations.append(f"🔴 ATR Filter: {atr_data['percentage']:.1f}% of no-trades. Consider reducing ATR threshold from {atr_data['threshold']} to {new_threshold:.1f} pips.")
            else:
                recommendations.append(f"🔴 ATR Filter: {atr_data['percentage']:.1f}% of no-trades. Consider reducing ATR threshold from {atr_data['threshold']} to 5 pips.")
        
        # Spread recommendations  
        spread_data = filter_triggers.get("spread_violations", {})
        if spread_data.get("percentage", 0) > 20:
            recommendations.append(f"🟡 Spread Filter: {spread_data['percentage']:.1f}% of no-trades. Consider increasing spread tolerance from {spread_data['threshold']} to 3 pips.")
        
        # News window recommendations
        news_data = filter_triggers.get("news_window_violations", {})
        if news_data.get("percentage", 0) > 25:
            recommendations.append(f"🟡 News Window Filter: {news_data['percentage']:.1f}% of no-trades. Consider reducing news window restrictions or making them more specific.")
        
        # Build-up recommendations
        buildup_data = filter_triggers.get("buildup_violations", {})
        if buildup_data.get("percentage", 0) > 40:
            avg_width = buildup_data.get("avg_width", 0)
            avg_bars = buildup_data.get("avg_bars", 0)
            if avg_width > 0:
                new_width = max(5, avg_width * 0.7)  # Reduce by 30% but minimum 5
                recommendations.append(f"🔴 Build-up Filter: {buildup_data['percentage']:.1f}% of no-trades. Consider reducing width threshold from {buildup_data['min_width_threshold']} to {new_width:.1f} pips.")
            if avg_bars > 0:
                new_bars = max(5, int(avg_bars * 0.7))  # Reduce by 30% but minimum 5
                recommendations.append(f"🔴 Build-up Filter: Consider reducing bars threshold from {buildup_data['min_bars_threshold']} to {new_bars} bars.")
        
        # Time pattern recommendations
        time_patterns = analysis.get("time_patterns", {})
        peak_hours = time_patterns.get("peak_no_trade_hours", [])
        if peak_hours:
            top_hour = peak_hours[0][0]
            top_count = peak_hours[0][1]
            total_no_trades = sum(analysis["time_patterns"]["no_trade_hourly"].values())
            if top_count / total_no_trades > 0.3:  # If one hour accounts for >30% of no-trades
                recommendations.append(f"⏰ Time Pattern: Hour {top_hour}:00 JST accounts for {top_count} ({top_count/total_no_trades*100:.1f}%) of no-trades. Consider adjusting news window restrictions for this hour.")
        
        # Overall filter efficiency
        total_entries = analysis["total_entries"]
        no_trade_entries = analysis["no_trade_entries"]
        if no_trade_entries / total_entries > 0.9:  # >90% no-trades
            recommendations.append(f"🚨 CRITICAL: {no_trade_entries/total_entries*100:.1f}% of all entries are no-trades. Filters are too restrictive - consider relaxing multiple thresholds simultaneously.")
        
        return recommendations
    
    def run_analysis(self, weeks_back: int = 3) -> Dict:
        """
        Run complete filter analysis.
        
        Args:
            weeks_back: Number of weeks to analyze
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting filter analysis for past {weeks_back} weeks")
        
        # Step 1: Fetch data
        pages = self.fetch_recent_entries(weeks_back)
        if not pages:
            logger.error("No entries found")
            return {"error": "No entries found"}
        
        # Step 2: Extract data
        df = self.extract_entry_data(pages)
        if df.empty:
            logger.error("No data extracted")
            return {"error": "No data extracted"}
        
        # Step 3: Analyze filters
        analysis = self.analyze_filter_triggers(df)
        
        # Step 4: Generate recommendations
        recommendations = self.generate_recommendations(analysis)
        analysis["recommendations"] = recommendations
        
        # Add metadata
        analysis["analysis_date"] = datetime.now(self.jst).isoformat()
        analysis["weeks_analyzed"] = weeks_back
        analysis["date_range"] = {
            "start": df["date"].min() if not df["date"].isna().all() else "Unknown",
            "end": df["date"].max() if not df["date"].isna().all() else "Unknown"
        }
        
        return analysis
    
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
    
    def _get_date_property(self, prop: Optional[Dict]) -> Optional[str]:
        """Extract date from Notion property."""
        if not prop or "date" not in prop:
            return None
        
        date_obj = prop["date"]
        if date_obj:
            return date_obj.get("start")
        
        return None
    
    def _extract_from_summary(self, summary_prop: Optional[Dict], keyword: str) -> Optional[float]:
        """Extract numeric values from summary text."""
        summary = self._get_text_property(summary_prop)
        if not summary:
            return None
        
        return self._extract_numeric_from_text(summary, f"{keyword}.*?([0-9.]+)")
    
    def _extract_numeric_from_text(self, text: str, pattern: str) -> Optional[float]:
        """Extract numeric value from text using regex pattern."""
        if not text:
            return None
        
        import re
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                pass
        return None


def main():
    """Main entry point."""
    print("🔍 FX Filter Analysis - Notion Database Analyzer")
    print("=" * 60)
    
    # Validate configuration
    if not config.notion_api_key or not config.notion_db_id:
        print("❌ Error: Notion API key or database ID not configured")
        print("Please set NOTION_API_KEY and NOTION_DB_ID environment variables")
        return
    
    try:
        # Initialize analyzer
        analyzer = NotionFilterAnalyzer()
        
        # Run analysis
        results = analyzer.run_analysis(weeks_back=3)
        
        if "error" in results:
            print(f"❌ Analysis failed: {results['error']}")
            return
        
        # Print results
        print("\n📊 ANALYSIS RESULTS")
        print("=" * 60)
        
        print(f"📅 Analysis Period: {results['date_range']['start']} to {results['date_range']['end']}")
        print(f"📈 Total Entries: {results['total_entries']}")
        print(f"🚫 No-Trade Entries: {results['no_trade_entries']} ({results['no_trade_entries']/results['total_entries']*100:.1f}%)")
        print(f"✅ Trade Entries: {results['trade_entries']} ({results['trade_entries']/results['total_entries']*100:.1f}%)")
        
        print("\n🔍 FILTER TRIGGER ANALYSIS")
        print("=" * 40)
        
        filter_triggers = results["filter_triggers"]
        for filter_name, data in filter_triggers.items():
            print(f"\n{filter_name.upper().replace('_', ' ')}:")
            print(f"  Violations: {data['count']} ({data['percentage']:.1f}%)")
            if "avg_value" in data and data["avg_value"]:
                print(f"  Average Value: {data['avg_value']}")
            if "threshold" in data:
                print(f"  Current Threshold: {data['threshold']}")
        
        print("\n⏰ TIME PATTERNS")
        print("=" * 40)
        
        time_patterns = results["time_patterns"]
        print("Top hours with most no-trades:")
        for hour, count in time_patterns["peak_no_trade_hours"][:5]:
            total_at_hour = time_patterns["hourly_distribution"].get(hour, 0)
            percentage = (count / total_at_hour * 100) if total_at_hour > 0 else 0
            print(f"  {hour:02d}:00 JST: {count} no-trades out of {total_at_hour} total ({percentage:.1f}%)")
        
        print("\n🎯 SETUP DISTRIBUTION")
        print("=" * 40)
        
        setup_dist = results["setup_distribution"]
        for setup, count in sorted(setup_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = count / results['total_entries'] * 100
            print(f"  {setup}: {count} ({percentage:.1f}%)")
        
        print("\n💡 RECOMMENDATIONS")
        print("=" * 40)
        
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")
        
        # Save results to file
        output_file = "filter_analysis_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Full results saved to: {output_file}")
        
        print("\n" + "=" * 60)
        print("✅ Analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"❌ Analysis failed: {e}")


if __name__ == "__main__":
    main()