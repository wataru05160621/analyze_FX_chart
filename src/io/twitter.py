"""
X (Twitter) integration with proper API v1.1 and v2 usage
修正5: media_upload is v1.1, create_tweet is v2
"""

import os
import tweepy
from typing import Dict, Optional, Tuple
from PIL import Image
import io
import requests

from src.utils.config import config
from src.utils.logger import get_logger
from src.guards.linguistic import LinguisticGuard

logger = get_logger(__name__)


class TwitterClient:
    """X (Twitter) client with v1.1 for media and v2 for tweets"""
    
    def __init__(self):
        """Initialize both API v1.1 and v2 clients"""
        
        # Get credentials from environment
        self.api_key = os.environ.get('TWITTER_API_KEY')
        self.api_secret = os.environ.get('TWITTER_API_SECRET')
        self.access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        self.access_secret = os.environ.get('TWITTER_ACCESS_SECRET')
        self.bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            logger.warning("Twitter credentials not configured")
            self.enabled = False
            return
        
        # Initialize v1.1 API for media upload (修正5)
        auth = tweepy.OAuth1UserHandler(
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_secret
        )
        self.api_v1 = tweepy.API(auth)
        
        # Initialize v2 client for tweets (修正5)
        self.client_v2 = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret
        )
        
        self.linguistic_guard = LinguisticGuard()
        self.enabled = True
        
        # Auto-post thresholds
        self.auto_post_threshold = {
            'ev_R': float(os.environ.get('TWITTER_MIN_EV_R', '0.5')),
            'confluence_count': int(os.environ.get('TWITTER_MIN_CONFLUENCE', '4')),
            'confidence': os.environ.get('TWITTER_MIN_CONFIDENCE', 'high'),
            'excluded_setups': ['No-Trade', 'F']
        }
        
        logger.info("Twitter client initialized", enabled=self.enabled)
    
    def should_post(self, analysis: Dict) -> Tuple[bool, str]:
        """
        Check if analysis meets auto-post criteria
        
        Returns:
            Tuple of (should_post, reason)
        """
        if not self.enabled:
            return False, "Twitter client not enabled"
        
        # Check setup exclusion
        if analysis.get('setup') in self.auto_post_threshold['excluded_setups']:
            return False, f"Setup {analysis.get('setup')} is excluded"
        
        # Check EV threshold
        if analysis.get('ev_R', 0) < self.auto_post_threshold['ev_R']:
            return False, f"EV {analysis.get('ev_R', 0)} below threshold {self.auto_post_threshold['ev_R']}"
        
        # Check confluence threshold
        if analysis.get('confluence_count', 0) < self.auto_post_threshold['confluence_count']:
            return False, f"Confluence {analysis.get('confluence_count', 0)} below threshold"
        
        # Check confidence threshold
        if analysis.get('confidence') != self.auto_post_threshold['confidence']:
            return False, f"Confidence {analysis.get('confidence')} not high enough"
        
        return True, "Meets all criteria"
    
    def post_analysis(self, analysis: Dict, chart_url: str = None, chart_path: str = None) -> Optional[str]:
        """
        Post analysis to X with chart
        
        Args:
            analysis: Analysis result dictionary
            chart_url: S3 URL of the chart (optional)
            chart_path: Local path to chart file (optional)
            
        Returns:
            Tweet ID if successful, None otherwise
        """
        try:
            # Check if should post
            should_post, reason = self.should_post(analysis)
            if not should_post:
                logger.info(f"Skipping Twitter post: {reason}")
                return None
            
            # Format tweet text
            text = self._format_tweet(analysis)
            
            # Apply linguistic guard
            text, flags = self.linguistic_guard.check_and_replace(text)
            if flags:
                logger.info(f"Linguistic guard applied: {flags}")
            
            # Upload media if available
            media_id = None
            if chart_path and os.path.exists(chart_path):
                media_id = self._upload_media_from_file(chart_path)
            elif chart_url:
                media_id = self._upload_media_from_url(chart_url)
            
            # Create tweet (修正5: v2 API)
            tweet_params = {'text': text}
            if media_id:
                tweet_params['media_ids'] = [str(media_id)]
            
            response = self.client_v2.create_tweet(**tweet_params)
            
            tweet_id = response.data['id']
            logger.info(f"Tweet posted successfully", tweet_id=tweet_id)
            
            return tweet_id
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {str(e)}")
            return None
    
    def _upload_media_from_file(self, file_path: str) -> Optional[int]:
        """
        Upload media from local file using v1.1 API
        修正5: Use v1.1 API for media upload
        """
        try:
            media = self.api_v1.media_upload(file_path)
            logger.info(f"Media uploaded", media_id=media.media_id)
            return media.media_id
        except Exception as e:
            logger.error(f"Failed to upload media: {str(e)}")
            return None
    
    def _upload_media_from_url(self, url: str) -> Optional[int]:
        """
        Download image from URL and upload to Twitter
        """
        try:
            # Download image
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            temp_path = f"/tmp/twitter_upload_{os.getpid()}.png"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Upload to Twitter
            media_id = self._upload_media_from_file(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            return media_id
            
        except Exception as e:
            logger.error(f"Failed to upload media from URL: {str(e)}")
            return None
    
    def _format_tweet(self, analysis: Dict) -> str:
        """
        Format analysis for tweet (max 280 characters)
        """
        setup_emoji = {
            'A': '🔥',  # Pattern Break
            'B': '📈',  # Pullback
            'C': '🔄',  # Probe Reversal
            'D': '⚡',  # Failed Break
            'E': '🚀',  # Momentum
            'F': '📊'   # Range Scalp
        }
        
        emoji = setup_emoji.get(analysis.get('setup', ''), '📊')
        pair = analysis.get('pair', 'USDJPY')
        setup = analysis.get('setup', 'Unknown')
        ev = analysis.get('ev_R', 0)
        confluence = analysis.get('confluence_count', 0)
        
        # Get first rationale (truncated)
        rationale = analysis.get('rationale', [''])[0]
        if len(rationale) > 80:
            rationale = rationale[:77] + "..."
        
        # Build tweet
        text = f"""{emoji} {pair} {setup} Setup Detected

EV: {ev:.2f}R | Confluence: {confluence}
{rationale}

#FX #{pair.replace('/', '')} #TechnicalAnalysis #AlgoTrading"""
        
        # Ensure within 280 character limit
        if len(text) > 280:
            # Truncate rationale further
            available = 280 - len(text) + len(rationale)
            rationale = rationale[:available-3] + "..."
            text = f"""{emoji} {pair} {setup} Setup

EV: {ev:.2f}R | Confluence: {confluence}
{rationale}

#FX #{pair.replace('/', '')} #AlgoTrading"""
        
        return text
    
    def post_weekly_summary(self, stats: Dict) -> Optional[str]:
        """Post weekly summary tweet"""
        try:
            text = f"""📊 Weekly FX Analysis Summary

Total Setups: {stats.get('total_setups', 0)}
High Quality: {stats.get('high_quality', 0)}
Win Rate: {stats.get('win_rate', 0):.1f}%
Best: {stats.get('best_setup', 'N/A')} ({stats.get('best_ev', 0):.2f}R)

#FXTrading #WeeklyReview #AlgoTrading"""
            
            response = self.client_v2.create_tweet(text=text)
            return response.data['id']
            
        except Exception as e:
            logger.error(f"Failed to post weekly summary: {str(e)}")
            return None