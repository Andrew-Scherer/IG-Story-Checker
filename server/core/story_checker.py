"""
Story Checker
Manages HTTP-based Instagram story checking
"""

import aiohttp
import json
import re
from typing import Optional, Dict, List
from datetime import datetime, UTC, timedelta

class SimpleStoryChecker:
    """Simple HTTP-based story checker"""
    
    def __init__(self, proxy: str, session_cookie: str):
        """Initialize checker with proxy and session
        
        Args:
            proxy: Proxy URL to use
            session_cookie: Instagram session cookie
        """
        self.proxy = proxy
        self.session_cookie = session_cookie
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_check: Optional[datetime] = None
        
        # Headers to look like a real browser with session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Cookie': f'sessionid={session_cookie}',
            'DNT': '1',
            'Sec-CH-UA': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
            'X-ASBD-ID': '129477',
            'X-IG-WWW-Claim': '0'
        }
    
    async def initialize(self) -> None:
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                proxy=self.proxy
            )
    
    async def check_story(self, username: str) -> bool:
        """Check if profile has story using Instagram API
        
        Args:
            username: Instagram username to check
            
        Returns:
            True if story found, False otherwise
            
        Raises:
            Exception: If check fails or rate limited
        """
        if not self.session:
            await self.initialize()
        
        try:
            # First get user ID from profile
            profile_url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
            
            async with self.session.get(profile_url) as response:
                if response.status == 429:
                    raise Exception("Rate limited")
                
                data = await response.json()
                if 'data' not in data or 'user' not in data['data']:
                    raise Exception("Failed to get user data")
                
                user = data['data']['user']
                user_id = user['id']
                
                # Get stories data
                stories_url = f'https://www.instagram.com/api/v1/feed/reels_media/?reel_ids={user_id}'
                
                async with self.session.get(stories_url) as stories_response:
                    if stories_response.status == 429:
                        raise Exception("Rate limited")
                    
                    stories_data = await stories_response.json()
                    
                    # Check if there are any stories
                    has_story = bool(stories_data.get('reels', {}).get(user_id, {}).get('items', []))
                    self.last_check = datetime.now(UTC)
                    return has_story
                    
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Failed to parse response")
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None

class ProxySessionPair:
    """Represents a proxy-session pair with health tracking"""
    
    def __init__(self, proxy: str, session_cookie: str):
        """Initialize proxy-session pair
        
        Args:
            proxy: Proxy URL to use
            session_cookie: Instagram session cookie
        """
        self.proxy = proxy
        self.session_cookie = session_cookie
        self.total_checks = 0
        self.successful_checks = 0
        self.last_used = None
        self.cooldown_until = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of checks"""
        if self.total_checks == 0:
            return 1.0
        return self.successful_checks / self.total_checks
    
    def record_success(self) -> None:
        """Record a successful check"""
        self.total_checks += 1
        self.successful_checks += 1
        self.last_used = datetime.now(UTC)
    
    def record_failure(self) -> None:
        """Record a failed check"""
        self.total_checks += 1
        self.last_used = datetime.now(UTC)
    
    def set_cooldown(self, minutes: int = 15) -> None:
        """Set cooldown period
        
        Args:
            minutes: Number of minutes to cooldown
        """
        self.cooldown_until = datetime.now(UTC) + timedelta(minutes=minutes)
    
    def is_on_cooldown(self) -> bool:
        """Check if pair is on cooldown"""
        if not self.cooldown_until:
            return False
        return datetime.now(UTC) < self.cooldown_until

class StoryChecker:
    """Main interface for Worker Manager"""
    
    def __init__(self, proxy: str, session_cookie: str):
        """Initialize story checker
        
        Args:
            proxy: Proxy URL to use
            session_cookie: Instagram session cookie
        """
        self.pair = ProxySessionPair(proxy, session_cookie)
        self.checker = SimpleStoryChecker(proxy, session_cookie)
        self.rate_limiter = BrowserRateLimiter()
    
    async def check_profile(self, username: str) -> bool:
        """Check if profile has story
        
        Args:
            username: Instagram username to check
            
        Returns:
            True if story found, False otherwise
            
        Raises:
            Exception: If check fails
        """
        # Check rate limits
        if self.pair.is_on_cooldown():
            raise Exception("Rate limited - On cooldown")
            
        if not self.rate_limiter.can_visit(self.pair.proxy):
            raise Exception("Rate limited - Too many requests")
        
        try:
            # Check story
            has_story = await self.checker.check_story(username)
            
            # Record success
            self.pair.record_success()
            self.rate_limiter.record_visit(self.pair.proxy)
            
            return has_story
            
        except Exception as e:
            # Record failure and handle rate limits
            self.pair.record_failure()
            if "Rate limited" in str(e):
                self.pair.set_cooldown()
                self.rate_limiter.handle_rate_limit(self.pair.proxy)
            raise

class BrowserRateLimiter:
    """Enforces browsing rate limits"""
    
    def __init__(self):
        """Initialize rate limiter"""
        self.visits: Dict[str, List[datetime]] = {}  # proxy -> visit times
        self.cooldowns: Dict[str, datetime] = {}  # proxy -> cooldown until
    
    def can_visit(self, proxy: str) -> bool:
        """Check if visit is allowed
        
        Args:
            proxy: Proxy to check
            
        Returns:
            True if visit allowed, False if rate limited
        """
        now = datetime.now(UTC)
        
        # Check cooldown
        if proxy in self.cooldowns:
            if now < self.cooldowns[proxy]:
                return False
            del self.cooldowns[proxy]
        
        # Initialize visit tracking
        if proxy not in self.visits:
            self.visits[proxy] = []
        
        # Clean old visits
        hour_ago = now - timedelta(hours=1)
        self.visits[proxy] = [
            time for time in self.visits[proxy]
            if time > hour_ago
        ]
        
        # Check hourly limit (100 per hour)
        if len(self.visits[proxy]) >= 100:
            return False
        
        # Check 30-minute limit (50 per 30 minutes)
        half_hour_ago = now - timedelta(minutes=30)
        recent_visits = len([
            time for time in self.visits[proxy]
            if time > half_hour_ago
        ])
        if recent_visits >= 50:
            return False
        
        # Check minimum delay (5 seconds)
        if self.visits[proxy]:
            last_visit = max(self.visits[proxy])
            if (now - last_visit).total_seconds() < 5:
                return False
        
        return True
    
    def record_visit(self, proxy: str) -> None:
        """Record a successful visit
        
        Args:
            proxy: Proxy that made the visit
        """
        if proxy not in self.visits:
            self.visits[proxy] = []
        self.visits[proxy].append(datetime.now(UTC))
    
    def handle_rate_limit(self, proxy: str) -> None:
        """Handle rate limit detection
        
        Args:
            proxy: Proxy that was rate limited
        """
        # Set 15-minute cooldown
        self.cooldowns[proxy] = datetime.now(UTC) + timedelta(minutes=15)
        
        # Clear visit history
        if proxy in self.visits:
            self.visits[proxy] = []
