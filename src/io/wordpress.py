"""
WordPress integration with proper media upload
修正6: Implement media upload and fix scope issues
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
import base64

from src.utils.logger import get_logger
from src.guards.linguistic import LinguisticGuard

logger = get_logger(__name__)


class WordPressClient:
    """WordPress client for creating draft posts with analysis"""
    
    def __init__(self):
        """Initialize WordPress client with REST API credentials"""
        
        # Get credentials from environment
        self.api_url = os.environ.get('WORDPRESS_API_URL')
        self.username = os.environ.get('WORDPRESS_USERNAME')
        self.app_password = os.environ.get('WORDPRESS_APP_PASSWORD')
        
        if not all([self.api_url, self.username, self.app_password]):
            logger.warning("WordPress credentials not configured")
            self.enabled = False
            return
        
        # Set up authentication
        self.auth = (self.username, self.app_password)
        self.headers = {
            'Content-Type': 'application/json',
        }
        
        self.linguistic_guard = LinguisticGuard()
        self.enabled = True
        
        # Configuration
        self.auto_publish = os.environ.get('WORDPRESS_AUTO_PUBLISH', 'false').lower() == 'true'
        self.default_category = os.environ.get('WORDPRESS_CATEGORY', 'FX Analysis')
        
        logger.info("WordPress client initialized", enabled=self.enabled, api_url=self.api_url)
    
    def create_draft_post(
        self,
        analysis: Dict,
        chart_urls: Optional[Dict[str, str]] = None,
        chart_paths: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Create a draft post with analysis
        
        Args:
            analysis: Analysis result dictionary
            chart_urls: Dict of timeframe to S3 URLs
            chart_paths: Dict of timeframe to local file paths
            
        Returns:
            Post URL if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("WordPress client not enabled")
            return None
        
        try:
            # Upload media files first (修正6)
            media_ids = self._upload_media_files(analysis, chart_urls, chart_paths)
            
            # Generate content with media IDs
            content = self._generate_content(analysis, media_ids)
            
            # Apply linguistic guard
            content, flags = self.linguistic_guard.check_and_replace(content)
            if flags:
                logger.info(f"Linguistic guard applied to content: {flags}")
            
            # Get category ID
            category_id = self._get_or_create_category(self.default_category)
            
            # Get tags
            tag_ids = self._get_or_create_tags(analysis)
            
            # Create post
            post_data = {
                'title': self._generate_title(analysis),
                'content': content,
                'status': 'publish' if self.auto_publish else 'draft',
                'categories': [category_id] if category_id else [],
                'tags': tag_ids,
                'featured_media': media_ids[0] if media_ids else None,
                'meta': {
                    'fx_analysis_run_id': analysis.get('run_id'),
                    'fx_analysis_setup': analysis.get('setup'),
                    'fx_analysis_ev': str(analysis.get('ev_R', 0))
                }
            }
            
            response = requests.post(
                f"{self.api_url}/wp-json/wp/v2/posts",
                json=post_data,
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code == 201:
                post = response.json()
                post_url = post.get('link')
                post_id = post.get('id')
                
                logger.info(f"WordPress post created", post_id=post_id, url=post_url)
                return post_url
            else:
                logger.error(f"Failed to create post: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"WordPress post creation failed: {str(e)}")
            return None
    
    def _upload_media_files(
        self,
        analysis: Dict,
        chart_urls: Optional[Dict[str, str]] = None,
        chart_paths: Optional[Dict[str, str]] = None
    ) -> List[int]:
        """
        Upload media files to WordPress
        修正6: Proper media upload implementation
        
        Returns:
            List of media IDs
        """
        media_ids = []
        
        # Upload from local files if available
        if chart_paths:
            for timeframe, path in chart_paths.items():
                if os.path.exists(path):
                    media_id = self._upload_media_file(
                        path,
                        f"{analysis.get('pair', 'USDJPY')}_{timeframe}_{analysis.get('run_id', 'unknown')[:8]}.png"
                    )
                    if media_id:
                        media_ids.append(media_id)
        
        # Upload from URLs if no local files
        elif chart_urls:
            for timeframe, url in chart_urls.items():
                media_id = self._upload_media_from_url(
                    url,
                    f"{analysis.get('pair', 'USDJPY')}_{timeframe}_{analysis.get('run_id', 'unknown')[:8]}.png"
                )
                if media_id:
                    media_ids.append(media_id)
        
        return media_ids
    
    def _upload_media_file(self, file_path: str, filename: str) -> Optional[int]:
        """
        Upload a single media file
        修正6: Multipart upload to /wp-json/wp/v2/media
        """
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, 'image/png')
                }
                
                response = requests.post(
                    f"{self.api_url}/wp-json/wp/v2/media",
                    files=files,
                    auth=self.auth,
                    timeout=60
                )
                
                if response.status_code == 201:
                    media = response.json()
                    media_id = media.get('id')
                    logger.info(f"Media uploaded", media_id=media_id, filename=filename)
                    return media_id
                else:
                    logger.error(f"Media upload failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to upload media file: {str(e)}")
            return None
    
    def _upload_media_from_url(self, url: str, filename: str) -> Optional[int]:
        """Upload media from URL by downloading first"""
        try:
            # Download image
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            temp_path = f"/tmp/wp_upload_{os.getpid()}.png"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Upload to WordPress
            media_id = self._upload_media_file(temp_path, filename)
            
            # Clean up
            os.remove(temp_path)
            
            return media_id
            
        except Exception as e:
            logger.error(f"Failed to upload media from URL: {str(e)}")
            return None
    
    def _generate_title(self, analysis: Dict) -> str:
        """Generate post title"""
        pair = analysis.get('pair', 'USDJPY')
        setup = analysis.get('setup', 'Analysis')
        date = datetime.now().strftime('%Y-%m-%d')
        
        return f"{pair} {setup} Setup Analysis - {date}"
    
    def _generate_content(self, analysis: Dict, media_ids: List[int]) -> str:
        """
        Generate WordPress content
        修正6: media_ids is now properly passed as parameter
        """
        
        # Build gallery shortcode if we have media
        gallery_html = ""
        if media_ids:
            gallery_html = f'[gallery ids="{",".join(map(str, media_ids))}"]'
        
        # Generate content
        content = f"""
<h2>Market Analysis Summary</h2>
<p><strong>Currency Pair:</strong> {analysis.get('pair', 'USDJPY')}<br>
<strong>Setup Type:</strong> {analysis.get('setup', 'Unknown')}<br>
<strong>Expected Value:</strong> {analysis.get('ev_R', 0):.2f}R<br>
<strong>Confluence Count:</strong> {analysis.get('confluence_count', 0)}<br>
<strong>Confidence Level:</strong> {analysis.get('confidence', 'Low')}</p>

<h2>Technical Setup Rationale</h2>
<ul>
{self._format_rationale_list(analysis.get('rationale', []))}
</ul>

<h2>Chart Analysis</h2>
{gallery_html}
<p>The charts above show the technical setup on both 5-minute and 1-hour timeframes, 
highlighting key levels and indicators used in this analysis.</p>

<h2>Trading Plan</h2>
{self._format_trading_plan(analysis.get('plan', {}))}

<h2>Risk Management</h2>
{self._format_risk_management(analysis)}

<h2>Market Environment</h2>
<p>Current market conditions show {self._describe_environment(analysis)}. 
This environment is {self._assess_favorability(analysis)} for the identified setup.</p>

<h2>Learning Notes</h2>
<p>This {analysis.get('setup', 'setup')} demonstrates several key trading principles:</p>
<ul>
<li><strong>Multiple Timeframe Analysis:</strong> Confirming setups across different timeframes increases probability</li>
<li><strong>Confluence Factors:</strong> The more supporting factors, the stronger the setup</li>
<li><strong>Risk Management:</strong> Always define stop loss and take profit levels before entry</li>
<li><strong>Quality Gates:</strong> Not all setups are worth trading - filters help avoid low-quality trades</li>
</ul>

<h3>Related Analysis</h3>
<p>For more {analysis.get('setup', '')} setup examples, see our previous analyses in this category.</p>

<hr>
<p><em>This analysis was generated automatically by our FX Analysis System. 
It represents technical analysis only and should not be considered as investment advice. 
Always conduct your own research and consider your risk tolerance before trading.</em></p>
"""
        
        return content
    
    def _format_rationale_list(self, rationale: List[str]) -> str:
        """Format rationale as HTML list items"""
        if not rationale:
            return "<li>No specific rationale provided</li>"
        
        items = []
        for reason in rationale[:5]:  # Limit to 5 items
            # Apply linguistic guard to each item
            clean_reason, _ = self.linguistic_guard.check_and_replace(reason)
            items.append(f"<li>{clean_reason}</li>")
        
        return "\n".join(items)
    
    def _format_trading_plan(self, plan: Dict) -> str:
        """Format trading plan as HTML"""
        if not plan:
            return "<p>No specific trading plan defined for this setup.</p>"
        
        return f"""
<table>
<tr><th>Entry Condition</th><td>{plan.get('entry', 'Not specified')}</td></tr>
<tr><th>Stop Loss</th><td>{plan.get('sl_pips', 0)} pips</td></tr>
<tr><th>Take Profit</th><td>{plan.get('tp_pips', 0)} pips</td></tr>
<tr><th>Timeout</th><td>{plan.get('timeout_min', 0)} minutes</td></tr>
</table>
"""
    
    def _format_risk_management(self, analysis: Dict) -> str:
        """Format risk management section"""
        risk = analysis.get('risk', {})
        ev = analysis.get('ev_R', 0)
        
        return f"""
<p><strong>Risk-Reward Ratio:</strong> {risk.get('r_multiple', 0):.2f}<br>
<strong>Expected Value:</strong> {ev:.2f}R<br>
<strong>Suggested Position Size:</strong> {risk.get('position_size', 0.01)} lots<br>
<strong>Maximum Risk:</strong> 1-2% of account per trade</p>
"""
    
    def _describe_environment(self, analysis: Dict) -> str:
        """Describe market environment"""
        indicators = analysis.get('indicators', {})
        atr = indicators.get('atr20', 0)
        
        if atr > 15:
            return "high volatility with strong directional movement potential"
        elif atr > 10:
            return "moderate volatility with good trading opportunities"
        else:
            return "low volatility, possibly range-bound conditions"
    
    def _assess_favorability(self, analysis: Dict) -> str:
        """Assess how favorable the environment is"""
        confluence = analysis.get('confluence_count', 0)
        confidence = analysis.get('confidence', 'low')
        
        if confidence == 'high' and confluence >= 4:
            return "highly favorable"
        elif confidence == 'medium' and confluence >= 3:
            return "moderately favorable"
        else:
            return "marginally favorable"
    
    def _get_or_create_category(self, category_name: str) -> Optional[int]:
        """Get or create category by name"""
        try:
            # Search for existing category
            response = requests.get(
                f"{self.api_url}/wp-json/wp/v2/categories",
                params={'search': category_name},
                auth=self.auth
            )
            
            if response.status_code == 200:
                categories = response.json()
                if categories:
                    return categories[0]['id']
            
            # Create new category
            response = requests.post(
                f"{self.api_url}/wp-json/wp/v2/categories",
                json={'name': category_name},
                auth=self.auth
            )
            
            if response.status_code == 201:
                return response.json()['id']
                
        except Exception as e:
            logger.error(f"Category creation failed: {str(e)}")
        
        return None
    
    def _get_or_create_tags(self, analysis: Dict) -> List[int]:
        """Get or create tags for the analysis"""
        tag_names = [
            analysis.get('pair', 'USDJPY'),
            analysis.get('setup', 'Unknown'),
            f"EV_{analysis.get('ev_R', 0):.1f}R",
            analysis.get('confidence', 'low')
        ]
        
        tag_ids = []
        for tag_name in tag_names:
            try:
                # Search for existing tag
                response = requests.get(
                    f"{self.api_url}/wp-json/wp/v2/tags",
                    params={'search': tag_name},
                    auth=self.auth
                )
                
                if response.status_code == 200:
                    tags = response.json()
                    if tags:
                        tag_ids.append(tags[0]['id'])
                        continue
                
                # Create new tag
                response = requests.post(
                    f"{self.api_url}/wp-json/wp/v2/tags",
                    json={'name': tag_name},
                    auth=self.auth
                )
                
                if response.status_code == 201:
                    tag_ids.append(response.json()['id'])
                    
            except Exception as e:
                logger.error(f"Tag creation failed for {tag_name}: {str(e)}")
        
        return tag_ids