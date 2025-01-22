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
        """Get full proxy URL with auth if available"""
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
    """
    # Query for active proxy with valid session
    proxy_session = Proxy.query.filter_by(is_active=True).join(Session).first()
    if not proxy_session:
        current_app.logger.warning('No active proxy-session pairs found')
        return None
        
    proxy, session = proxy_session
    return ProxySession(proxy, session)
