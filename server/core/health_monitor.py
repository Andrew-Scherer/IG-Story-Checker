"""
Health Monitor
Handles proxy health monitoring and cleanup
"""

from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from models.proxy import Proxy, ProxyStatus

class HealthMonitor:
    """Manages proxy health monitoring and cleanup"""

    ERROR_THRESHOLD = 5  # Max errors before marking proxy as unhealthy
    HOURLY_LIMIT = 150  # Maximum requests per hour
    COOLDOWN_MINUTES = 15  # Minutes to cooldown after rate limit

    def __init__(self, db_session: Session):
        """Initialize HealthMonitor
        
        Args:
            db_session: Database session for proxy operations
        """
        self.db = db_session

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
