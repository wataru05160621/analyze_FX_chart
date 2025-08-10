"""S3 storage operations."""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError

from src.utils.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class S3Client:
    """S3 client for storing analysis artifacts."""
    
    def __init__(self, bucket: Optional[str] = None, region: Optional[str] = None):
        """Initialize S3 client."""
        self.bucket = bucket or config.s3_bucket
        self.region = region or config.aws_region
        
        if not self.bucket:
            raise ValueError("S3_BUCKET is required")
        
        self.s3 = boto3.client('s3', region_name=self.region)
        
    def upload_chart(
        self,
        chart_bytes: bytes,
        pair: str,
        run_id: str,
        timeframe: str,
        date: Optional[datetime] = None
    ) -> str:
        """
        Upload chart to S3 and return key.
        
        Args:
            chart_bytes: PNG image bytes
            pair: Trading pair
            run_id: Unique run ID
            timeframe: Timeframe (e.g., "5m", "1h")
            date: Date for organization (defaults to today)
            
        Returns:
            S3 object key
        """
        if date is None:
            date = datetime.now()
        
        # Build S3 key: charts/{pair}/{yyyy-mm-dd}/{run_id}_{timeframe}.png
        date_str = date.strftime("%Y-%m-%d")
        key = f"{config.s3_prefix}/{pair}/{date_str}/{run_id}_{timeframe}.png"
        
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=chart_bytes,
                ContentType='image/png',
                Metadata={
                    'pair': pair,
                    'timeframe': timeframe,
                    'run_id': run_id
                }
            )
            logger.info(f"Uploaded chart to S3", key=key, size=len(chart_bytes))
            return key
            
        except ClientError as e:
            logger.error(f"Failed to upload chart to S3", error=str(e), key=key)
            raise
    
    def upload_json(
        self,
        data: Dict,
        pair: str,
        run_id: str,
        date: Optional[datetime] = None
    ) -> str:
        """
        Upload JSON analysis results to S3.
        
        Args:
            data: Analysis results dict
            pair: Trading pair
            run_id: Unique run ID
            date: Date for organization
            
        Returns:
            S3 object key
        """
        if date is None:
            date = datetime.now()
        
        # Build S3 key
        date_str = date.strftime("%Y-%m-%d")
        key = f"{config.s3_prefix}/{pair}/{date_str}/{run_id}_analysis.json"
        
        # Convert to JSON
        json_str = json.dumps(data, indent=2, default=str)
        
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json_str.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'pair': pair,
                    'run_id': run_id
                }
            )
            logger.info(f"Uploaded JSON to S3", key=key)
            return key
            
        except ClientError as e:
            logger.error(f"Failed to upload JSON to S3", error=str(e), key=key)
            raise
    
    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate a pre-signed URL for S3 object.
        
        Args:
            key: S3 object key
            expiration: URL expiration in seconds (default 1 hour)
            
        Returns:
            Pre-signed URL
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )
            logger.info(f"Generated pre-signed URL", key=key, expires_in=expiration)
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate pre-signed URL", error=str(e), key=key)
            raise
    
    def upload_analysis_artifacts(
        self,
        analysis: Dict,
        charts: Dict[str, bytes],
        pair: Optional[str] = None
    ) -> Dict:
        """
        Upload all analysis artifacts and return URLs.
        
        Args:
            analysis: Analysis results
            charts: Dict of timeframe to chart bytes
            pair: Trading pair (defaults to config)
            
        Returns:
            Dict with uploaded keys and pre-signed URLs
        """
        pair = pair or config.pair
        run_id = analysis.get("run_id", "unknown")
        date = datetime.now()
        
        results = {
            "charts": {},
            "json": None
        }
        
        # Upload charts
        for timeframe, chart_bytes in charts.items():
            try:
                key = self.upload_chart(chart_bytes, pair, run_id, timeframe, date)
                url = self.generate_presigned_url(key, expiration=3600)  # 1 hour
                results["charts"][timeframe] = {
                    "key": key,
                    "url": url
                }
            except Exception as e:
                logger.error(f"Failed to upload {timeframe} chart", error=str(e))
                # Continue with other uploads
        
        # Add chart URLs to analysis
        analysis["charts"] = results["charts"]
        
        # Upload JSON
        try:
            json_key = self.upload_json(analysis, pair, run_id, date)
            json_url = self.generate_presigned_url(json_key, expiration=3600)
            results["json"] = {
                "key": json_key,
                "url": json_url
            }
        except Exception as e:
            logger.error(f"Failed to upload JSON", error=str(e))
        
        logger.info(
            "Uploaded analysis artifacts",
            run_id=run_id,
            charts_count=len(results["charts"]),
            has_json=results["json"] is not None
        )
        
        return results