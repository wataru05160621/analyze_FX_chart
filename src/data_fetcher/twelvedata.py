"""TwelveData API client for fetching FX data."""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd
import pytz
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TwelveDataClient:
    """Client for TwelveData API."""
    
    BASE_URL = "https://api.twelvedata.com"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize TwelveData client."""
        self.api_key = api_key or config.twelvedata_api_key
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY is required")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"apikey {self.api_key}"
        })
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request with retry logic."""
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        logger.info("Making TwelveData API request", endpoint=endpoint, params=params)
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if "status" in data and data["status"] == "error":
            error_msg = data.get("message", "Unknown API error")
            logger.error("TwelveData API error", error=error_msg)
            raise ValueError(f"TwelveData API error: {error_msg}")
        
        return data
    
    def fetch_timeseries(
        self, 
        symbol: str, 
        interval: str,
        outputsize: int = 200,
        timezone: str = "Asia/Tokyo"
    ) -> pd.DataFrame:
        """
        Fetch time series data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "USD/JPY")
            interval: Time interval (e.g., "5min", "1h")
            outputsize: Number of data points to fetch
            timezone: Timezone for the data
            
        Returns:
            DataFrame with OHLCV data, index in JST
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "timezone": timezone,
            "format": "JSON"
        }
        
        data = self._request("time_series", params)
        
        # Parse response
        if "values" not in data:
            logger.error("No values in TwelveData response", response=data)
            raise ValueError("No data returned from TwelveData API")
        
        # Convert to DataFrame
        df = pd.DataFrame(data["values"])
        
        # Convert string columns to numeric
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Parse datetime and set as index
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        
        # Sort by time (ascending)
        df.sort_index(inplace=True)
        
        # Ensure timezone awareness
        if df.index.tz is None:
            jst = pytz.timezone(timezone)
            df.index = df.index.tz_localize(jst)
        
        logger.info(
            "Fetched time series data",
            symbol=symbol,
            interval=interval,
            rows=len(df),
            start=df.index[0] if len(df) > 0 else None,
            end=df.index[-1] if len(df) > 0 else None
        )
        
        return df
    
    def fetch_quote(self, symbol: str) -> Dict:
        """
        Fetch current quote for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "USD/JPY")
            
        Returns:
            Dict with current price data
        """
        params = {
            "symbol": symbol,
            "format": "JSON"
        }
        
        data = self._request("quote", params)
        
        # Convert numeric fields
        numeric_fields = ["open", "high", "low", "close", "volume", "previous_close", "change", "percent_change"]
        for field in numeric_fields:
            if field in data:
                data[field] = float(data[field]) if data[field] else None
        
        logger.info("Fetched quote", symbol=symbol, price=data.get("close"))
        
        return data


def fetch_multi_timeframe_data(
    symbol: Optional[str] = None,
    timeframes: Optional[list] = None
) -> Dict[str, pd.DataFrame]:
    """
    Fetch data for multiple timeframes.
    
    Args:
        symbol: Trading symbol (defaults to config)
        timeframes: List of timeframes (defaults to config)
        
    Returns:
        Dict mapping timeframe to DataFrame
    """
    symbol = symbol or config.symbol
    timeframes = timeframes or config.timeframes
    
    client = TwelveDataClient()
    data = {}
    
    for tf in timeframes:
        try:
            # Map timeframe format if needed
            interval = tf.replace("m", "min") if "m" in tf else tf
            df = client.fetch_timeseries(symbol, interval)
            data[tf] = df
        except Exception as e:
            logger.error(f"Failed to fetch {tf} data", error=str(e))
            raise
    
    return data