"""
Proxy Retriever
Handles proxy retrieval and rotation logic
"""

from typing import List, Optional
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from models.proxy import Proxy, ProxyStatus

class ProxyRetriever:
    """Manages retrieval and rotation of proxies"""

    def __init__(self, db_session: Session):
        """Initialize ProxyRetriever
        
        Args:
            db_session: Database session for proxy operations
        """
        self.db = db_session
        self.last_proxy_index = -1  # For round-robin rotation

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
        """Get next available proxy using round-robin rotation
        
        Returns:
            Next proxy to use, or None if none available
        """
        # Get available proxies
        proxies = self.get_available_proxies()
        if not proxies:
            return None
        
        # Implement round-robin selection
        self.last_proxy_index = (self.last_proxy_index + 1) % len(proxies)
        next_proxy = proxies[self.last_proxy_index]
        # Update last used time
        next_proxy.last_used = datetime.now(UTC)
        self.db.commit()
        return next_proxy
