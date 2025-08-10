"""Configuration management for FX Analysis system."""

import os
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Application configuration."""
    
    # App settings
    app_name: str = os.getenv("APP_NAME", "analyze-fx")
    tz: str = os.getenv("TZ", "Asia/Tokyo")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Trading pairs
    pair: str = os.getenv("PAIR", "USDJPY")
    symbol: str = os.getenv("SYMBOL", "USD/JPY")
    timeframes: List[str] = os.getenv("TIMEFRAMES", "5m,1h").split(",")
    
    # Data source
    data_source: str = os.getenv("DATA_SOURCE", "twelvedata")
    twelvedata_api_key: str = os.getenv("TWELVEDATA_API_KEY", "")
    
    # AWS
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    s3_prefix: str = os.getenv("S3_PREFIX", "charts")
    aws_region: str = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    
    # Notion
    notion_api_key: str = os.getenv("NOTION_API_KEY", "")
    notion_db_id: str = os.getenv("NOTION_DB_ID", "")
    
    # Slack
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    
    # Model
    model_api_key: Optional[str] = os.getenv("MODEL_API_KEY")
    
    def validate(self) -> None:
        """Validate required configuration."""
        required = {
            "TWELVEDATA_API_KEY": self.twelvedata_api_key,
            "S3_BUCKET": self.s3_bucket,
            "NOTION_API_KEY": self.notion_api_key,
            "NOTION_DB_ID": self.notion_db_id,
        }
        
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

# Global config instance
config = Config()