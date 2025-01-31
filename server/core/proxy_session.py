"""
Proxy Session Manager
Manages proxy sessions for story checking
"""

from typing import Optional, Tuple
from datetime import datetime, timezone
from models.proxy import Proxy
from models.session import Session
from flask import current_app

class ProxySession:
    """Manages a proxy-session pair with health tracking"""
    
    def __init__(self, proxy: Proxy, session: Session):
        """Initialize proxy session
        
        Args:
            proxy: Proxy model instance
            session: Session model instance
        """
        self.proxy = proxy
        self.session = session
        self.last_used: Optional[datetime] = None
        
    @property
    def proxy_url(self) -> str:
        """Get full HTTP proxy URL with auth if available (for session manager)"""
        # Ensure IP does not include protocol prefix
        ip = self.proxy.ip
        if ip.startswith('http://') or ip.startswith('socks5://'):
            ip = ip.split('://')[-1]
        if self.proxy.username and self.proxy.password:
            return f"http://{self.proxy.username}:{self.proxy.password}@{ip}:{self.proxy.port}"
        return f"http://{ip}:{self.proxy.port}"

    @property
    def socks5_url(self) -> str:
        """Get full SOCKS5 proxy URL with auth if available (for ProxyConnector)"""
        # Ensure IP does not include protocol prefix
        ip = self.proxy.ip
        if ip.startswith('http://') or ip.startswith('socks5://'):
            ip = ip.split('://')[-1]
        if self.proxy.username and self.proxy.password:
            return f"socks5://{self.proxy.username}:{self.proxy.password}@{ip}:{self.proxy.port}"
        return f"socks5://{ip}:{self.proxy.port}"
        
    @property
    def proxy_url_safe(self) -> str:
        """Get proxy URL safe for logging (without credentials)"""
        return f"{self.proxy.ip}:{self.proxy.port}"
        
    def record_success(self) -> None:
        """Record a successful request"""
        self.proxy.record_request(success=True)
        self.last_used = datetime.now(timezone.utc)
        current_app.logger.debug(f'Recorded successful request for proxy {self.proxy_url_safe}')
        
    def record_failure(self) -> None:
        """Record a failed request"""
        self.proxy.record_request(success=False)
        self.last_used = datetime.now(timezone.utc)
        current_app.logger.debug(f'Recorded failed request for proxy {self.proxy_url_safe}')

def get_available_proxy_session() -> Optional[ProxySession]:
    """Get an available proxy-session pair from the database
    
    Returns:
        ProxySession if available, None if no valid pairs found
        
    Selection criteria:
    - Must be active and not disabled/rate-limited
    - Must be under hourly request limit
    - Must have succeeded before or be new
    - Ordered by least recently used, lowest request count, fewest errors
    """
    # Query for active, non-disabled proxies with valid sessions
    proxy_session = (
        Proxy.query
        .filter(
            # Must be active
            Proxy.is_active == True,
            # Must not be disabled or rate limited
            Proxy._status.in_([ProxyStatus.ACTIVE.value]),
            # Must be under rate limit
            Proxy.requests_this_hour < Proxy.HOURLY_LIMIT,
            # Must have had recent success or be new
            (
                Proxy.last_success.isnot(None) |  # Has succeeded before
                Proxy.total_requests == 0  # Or is new
            )
        )
        .join(Session)  # Must have valid session
        .order_by(
            # Prefer proxies with:
            Proxy.last_used.asc().nullsfirst(),  # Least recently used first
            Proxy.requests_this_hour.asc(),  # Lower request count
            Proxy.error_count.asc()  # Fewer errors
        )
        .first()
    )

    if not proxy_session:
        current_app.logger.warning('No available proxy-session pairs found')
        return None
        
    proxy, session = proxy_session
    current_app.logger.info(
        f'Selected proxy {proxy.ip}:{proxy.port} '
        f'(requests: {proxy.requests_this_hour}/{proxy.HOURLY_LIMIT}, '
        f'errors: {proxy.error_count})'
    )
    return ProxySession(proxy, session)
