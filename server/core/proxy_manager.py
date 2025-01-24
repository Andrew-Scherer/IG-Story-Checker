"""
Proxy Manager
Coordinates proxy operations by utilizing specialized modules.
"""

from typing import Optional, Dict
from sqlalchemy.orm import Session
from models.proxy import Proxy, ProxyStatus
from core.proxy_retriever import ProxyRetriever
from core.health_monitor import HealthMonitor
from core.session_manager import SessionManager
from core.metrics_collector import MetricsCollector
from core.story_checker import StoryChecker
from datetime import datetime, timedelta, UTC

class ProxyManager:
    """High-level proxy manager that orchestrates proxy operations using specialized modules."""

    def __init__(self, db_session: Session):
        """Initialize ProxyManager

        Args:
            db_session: Database session for proxy operations
        """
        self.db = db_session
        self.proxy_retriever = ProxyRetriever(db_session)
        self.health_monitor = HealthMonitor(db_session)
        self.session_manager = SessionManager()
        self.metrics_collector = MetricsCollector()

    def get_next_proxy(self) -> Optional[Proxy]:
        """Get next available proxy using the proxy retriever"""
        proxy = self.proxy_retriever.get_next_proxy()
        if proxy is None:
            return None

        # Update last used time in session manager
        proxy_url = f"http://{proxy.ip}:{proxy.port}"
        self.session_manager.update_last_used(proxy_url)

        return proxy

    def is_proxy_healthy(self, proxy: Proxy) -> bool:
        """Check if proxy is healthy using the health monitor"""
        return self.health_monitor.is_proxy_healthy(proxy)

    def create_story_checker(self, proxy: Proxy) -> Optional[StoryChecker]:
        """Create StoryChecker for proxy

        Args:
            proxy: Proxy to create checker for

        Returns:
            StoryChecker instance, or None if proxy has no session
        """
        # Get session cookie from session manager
        proxy_url = f"http://{proxy.ip}:{proxy.port}"
        session_data = self.session_manager.get_session(proxy_url)
        if not session_data:
            return None
        session_cookie, _ = session_data

        # Create base URL
        base_url = f"http://{proxy.ip}:{proxy.port}"

        # Create StoryChecker
        checker = StoryChecker(
            proxy=base_url,
            session_cookie=session_cookie
        )

        return checker

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
        # Update metrics
        proxy_url = f"http://{proxy.ip}:{proxy.port}"
        self.metrics_collector.record_proxy_usage(proxy_url)
        if success:
            self.metrics_collector.record_proxy_success(proxy_url)
        if response_time is not None:
            self.metrics_collector.record_response_time(proxy_url, response_time)
        if not success and error:
            if 'rate limit' in error.lower():
                self.metrics_collector.record_rate_limit(proxy_url)
                # Update proxy status in health monitor
                self.health_monitor.update_proxy_status(proxy, rate_limited=True)
            else:
                # Handle other errors (e.g., increase error count)
                proxy.error_count = (proxy.error_count or 0) + 1

        # Update proxy statistics in the database
        if proxy.total_requests is None:
            proxy.total_requests = 0
        if proxy.failed_requests is None:
            proxy.failed_requests = 0
        if proxy.requests_this_hour is None:
            proxy.requests_this_hour = 0
        if proxy.error_count is None:
            proxy.error_count = 0

        proxy.total_requests += 1
        proxy.requests_this_hour += 1
        if not success:
            proxy.failed_requests += 1

        # Check for hourly limit and error thresholds
        if proxy.requests_this_hour >= self.health_monitor.HOURLY_LIMIT:
            proxy.status = ProxyStatus.RATE_LIMITED
            proxy.cooldown_until = datetime.now(UTC) + timedelta(minutes=self.health_monitor.COOLDOWN_MINUTES)

        if proxy.error_count >= self.health_monitor.ERROR_THRESHOLD:
            proxy.status = ProxyStatus.DISABLED

        self.db.commit()

    def get_proxy_metrics(self, proxy: Proxy) -> Dict[str, float]:
        """Get metrics for a specific proxy

        Args:
            proxy: Proxy to get metrics for

        Returns:
            Dictionary of metrics
        """
        proxy_url = f"http://{proxy.ip}:{proxy.port}"
        return self.metrics_collector.get_proxy_metrics(proxy_url)

    def cleanup_proxies(self):
        """Cleanup proxies using the health monitor"""
        self.health_monitor.cleanup_proxies()
