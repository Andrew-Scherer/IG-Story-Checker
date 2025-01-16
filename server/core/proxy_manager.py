"""
Proxy Manager
Manages proxy pool, health monitoring, and rotation strategies
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from models.proxy import Proxy, ProxyStatus
from core.story_checker import StoryChecker

class ProxyManager:
    """Manages pool of proxies with health monitoring and rotation"""
    
    # Constants
    ERROR_THRESHOLD = 5  # Max errors before marking proxy as unhealthy
    HOURLY_LIMIT = 150  # Maximum requests per hour
    COOLDOWN_MINUTES = 15  # Minutes to cooldown after rate limit
    
    def __init__(self, db_session: Session):
        """Initialize proxy manager
        
        Args:
            db_session: Database session for proxy operations
        """
        self.db = db_session
    
    def get_available_proxies(self) -> List[Proxy]:
        """Get list of available proxies
        
        Returns:
            List of proxies that are active and not rate limited
        """
        # Get all proxies
        proxies = self.db.query(Proxy).all()
        
        # Filter active proxies not on cooldown
        now = datetime.now(UTC)
        available = []
        for proxy in proxies:
            # Reset status if cooldown expired
            if (proxy.status == ProxyStatus.RATE_LIMITED and 
                proxy.cooldown_until and proxy.cooldown_until <= now):
                proxy.status = ProxyStatus.ACTIVE
                proxy.cooldown_until = None
                self.db.commit()
            
            if proxy.status == ProxyStatus.ACTIVE:
                available.append(proxy)
        
        return available
    
    def get_next_proxy(self) -> Optional[Proxy]:
        """Get next available proxy using load balancing
        
        Returns:
            Next proxy to use, or None if none available
        """
        # Get available proxies
        proxies = self.get_available_proxies()
        if not proxies:
            return None
            
        # Sort by total requests (ascending) and last used (oldest first)
        def sort_key(p):
            return (
                p.total_requests if p.total_requests is not None else 0,
                p.last_used if p.last_used is not None else datetime.min.replace(tzinfo=UTC)
            )
        
        proxies.sort(key=sort_key)
        return proxies[0]
    
    def is_proxy_healthy(self, proxy: Proxy) -> bool:
        """Check if proxy is healthy
        
        Args:
            proxy: Proxy to check
            
        Returns:
            True if proxy is healthy, False otherwise
        """
        if proxy.error_count is None:
            proxy.error_count = 0
            
        # Check error threshold
        if proxy.error_count >= self.ERROR_THRESHOLD:
            proxy.status = ProxyStatus.DISABLED
            return False
            
        # Check status
        if proxy.status == ProxyStatus.DISABLED:
            return False
            
        # Check cooldown
        now = datetime.now(UTC)
        if proxy.status == ProxyStatus.RATE_LIMITED:
            if proxy.cooldown_until and proxy.cooldown_until <= now:
                proxy.status = ProxyStatus.ACTIVE
                proxy.cooldown_until = None
                self.db.commit()
                return True
            return False
            
        return True
    
    def record_request(
        self,
        proxy: Proxy,
        success: bool,
        response_time: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Record proxy request result
        
        Args:
            proxy: Proxy that made request
            success: Whether request succeeded
            response_time: Response time in milliseconds (optional)
            error: Error message if failed (optional)
        """
        # Initialize counters if needed
        if proxy.total_requests is None:
            proxy.total_requests = 0
        if proxy.failed_requests is None:
            proxy.failed_requests = 0
        if proxy.requests_this_hour is None:
            proxy.requests_this_hour = 0
        if proxy.error_count is None:
            proxy.error_count = 0
        
        # Record request
        proxy.record_request(
            success=success,
            response_time=response_time,
            error=error
        )
        
        # Check rate limit
        if proxy.requests_this_hour >= self.HOURLY_LIMIT:
            proxy.status = ProxyStatus.RATE_LIMITED
            proxy.cooldown_until = datetime.now(UTC) + timedelta(minutes=self.COOLDOWN_MINUTES)
        
        # Check error threshold
        if proxy.error_count >= self.ERROR_THRESHOLD:
            proxy.status = ProxyStatus.DISABLED
        
        self.db.commit()
    
    def cleanup_proxies(self) -> None:
        """Mark unhealthy proxies as disabled"""
        # Get all proxies
        proxies = self.db.query(Proxy).all()
        
        # Update status of unhealthy proxies
        for proxy in proxies:
            if proxy.error_count is None:
                proxy.error_count = 0
            if proxy.error_count >= self.ERROR_THRESHOLD:
                proxy.status = ProxyStatus.DISABLED
        
        self.db.commit()
    
    def create_story_checker(self, proxy: Proxy) -> Optional[StoryChecker]:
        """Create StoryChecker for proxy
        
        Args:
            proxy: Proxy to create checker for
            
        Returns:
            StoryChecker instance, or None if proxy has no session
        """
        # Get proxy's session
        session = proxy.sessions[0] if proxy.sessions else None
        if not session:
            return None
        
        # Create base URL first
        base_url = f"http://{proxy.ip}:{proxy.port}"
        # Then add credentials
        proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
        
        # Create checker
        checker = StoryChecker(
            proxy=base_url,  # Use base URL without credentials
            session_cookie=session.session
        )
        
        return checker
    
    def get_proxy_metrics(self, proxy: Proxy) -> Dict:
        """Get proxy performance metrics
        
        Args:
            proxy: Proxy to get metrics for
            
        Returns:
            Dictionary of metrics
        """
        # Initialize metrics if needed
        if proxy.total_requests is None:
            proxy.total_requests = 0
        if proxy.failed_requests is None:
            proxy.failed_requests = 0
        if proxy.error_count is None:
            proxy.error_count = 0
        
        return {
            'success_rate': (
                (proxy.total_requests - proxy.failed_requests) / proxy.total_requests
                if proxy.total_requests > 0 else 1.0
            ),
            'avg_response_time': proxy.average_response_time,
            'total_requests': proxy.total_requests,
            'error_count': proxy.error_count,
            'status': proxy.status.value,
            'cooldown_until': proxy.cooldown_until,
            'last_error': proxy.last_error,
            'last_used': proxy.last_used
        }
