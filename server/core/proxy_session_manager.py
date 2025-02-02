"""
Proxy Session Manager
Combines proxy and session management for use within Celery tasks.
"""

from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from models.proxy import Proxy, ProxyStatus
from models import db
from core.proxy_retriever import ProxyRetriever
from core.health_monitor import HealthMonitor
from core.metrics_collector import MetricsCollector
from core.story_checker import StoryChecker
from flask import current_app

class ProxySessionManager:
    """Manages proxies and their sessions, designed for thread-safe operations within Celery tasks."""

    def __init__(self, db_session: Session):
        """Initialize ProxySessionManager

        Args:
            db_session: Database session for proxy operations
        """
        self.db = db_session
        self.proxy_retriever = ProxyRetriever(db_session)
        self.health_monitor = HealthMonitor(db_session)
        self.metrics_collector = MetricsCollector()

        # Thread-safe dictionaries for proxy sessions and last used times
        self.proxy_sessions: Dict[str, Dict] = {}  # proxy_url -> {session_cookie, proxy_id}
        self.last_used: Dict[str, datetime] = {}  # proxy_url -> last used time

        # Sync initial state
        self.sync_states()

    def _get_safe_proxy_url(self, proxy_url: str) -> str:
        """Normalize proxy URL format for consistent storage and retrieval."""
        # Remove protocol if present
        if '://' in proxy_url:
            proxy_url = proxy_url.split('://')[-1]
        # Remove credentials if present
        if '@' in proxy_url:
            proxy_url = proxy_url.split('@')[-1]
        return proxy_url

    def _normalize_proxy_url(self, proxy_url: str) -> str:
        """Get normalized proxy URL for storage and lookup."""
        return self._get_safe_proxy_url(proxy_url)

    def add_proxy(self, proxy_url: str, session_cookie: str) -> Optional[int]:
        """Add new proxy-session pair

        Args:
            proxy_url: Full proxy URL (e.g., socks5://proxy:8080)
            session_cookie: Session cookie

        Returns:
            Proxy ID if successful, None if proxy not found
        """
        current_app.logger.info(f'Adding proxy-session pair (proxy: {self._get_safe_proxy_url(proxy_url)})')

        try:
            # Get proxy ID from database using consistent format
            proxy_url_no_protocol = proxy_url.split('://')[-1]  # Remove protocol
            if '@' in proxy_url_no_protocol:  # Remove auth if present
                proxy_url_no_protocol = proxy_url_no_protocol.split('@')[-1]

            # Parse IP and port
            ip, port = proxy_url_no_protocol.split(':')
            port = int(port)

            current_app.logger.debug(f'Looking up proxy with ip={ip}, port={port}')
            proxy_obj = Proxy.query.filter_by(ip=ip, port=port).first()

            if not proxy_obj:
                current_app.logger.error(f'Proxy lookup failed - ip={ip}, port={port} not found in database')
                return None

            current_app.logger.info(f'Found proxy {proxy_obj.id} for {ip}:{port}')

            # Store with normalized URL
            normalized_url = self._normalize_proxy_url(proxy_url)
            current_app.logger.debug(f'Storing session with normalized URL: {normalized_url}')

            self.proxy_sessions[normalized_url] = {
                'session_cookie': session_cookie,
                'proxy_id': proxy_obj.id
            }
            self.last_used[normalized_url] = proxy_obj.last_used or datetime.min.replace(tzinfo=UTC)

            return proxy_obj.id

        except ValueError as e:
            current_app.logger.error(f'Error parsing proxy URL {self._get_safe_proxy_url(proxy_url)}: {str(e)}')
            return None
        except Exception as e:
            current_app.logger.error(f'Unexpected error adding proxy {self._get_safe_proxy_url(proxy_url)}: {str(e)}')
            return None

    def remove_proxy(self, proxy_url: str):
        """Remove proxy-session pair"""
        normalized_url = self._normalize_proxy_url(proxy_url)
        current_app.logger.info(f'Removing proxy-session pair (proxy: {normalized_url})')

        if normalized_url in self.proxy_sessions:
            current_app.logger.debug(f'Removing session data for {normalized_url}')
            del self.proxy_sessions[normalized_url]
        if normalized_url in self.last_used:
            current_app.logger.debug(f'Removing last used time for {normalized_url}')
            del self.last_used[normalized_url]

    def get_session(self, proxy_url: str) -> Optional[Tuple[str, int]]:
        """Get session cookie and proxy ID for proxy

        Args:
            proxy_url: Proxy URL (with or without protocol)

        Returns:
            Tuple of (session_cookie, proxy_id) if found, None if not
        """
        normalized_url = self._normalize_proxy_url(proxy_url)
        current_app.logger.debug(f'Looking up session for normalized proxy URL: {normalized_url}')

        session_data = self.proxy_sessions.get(normalized_url)
        if not session_data:
            current_app.logger.error(f'No session data found for proxy {normalized_url}')
            current_app.logger.debug(f'Available sessions: {list(self.proxy_sessions.keys())}')
            return None

        session_cookie = session_data.get('session_cookie')
        proxy_id = session_data.get('proxy_id')

        if not session_cookie or not proxy_id:
            current_app.logger.error(f'Invalid session data for proxy {normalized_url}: missing session cookie or proxy ID')
            return None

        current_app.logger.info(f'Found valid session for proxy {normalized_url}')
        current_app.logger.debug(f'Session data: {session_cookie[:10]}..., proxy_id: {proxy_id}')
        return session_cookie, proxy_id

    def update_last_used(self, proxy_url: str):
        """Update last used time for proxy"""
        normalized_url = self._normalize_proxy_url(proxy_url)
        current_app.logger.debug(f'Updating last used time for normalized proxy URL: {normalized_url}')

        if normalized_url not in self.proxy_sessions:
            current_app.logger.error(f'Cannot update last used time - no session found for proxy {normalized_url}')
            current_app.logger.debug(f'Available sessions: {list(self.proxy_sessions.keys())}')
            return

        self.last_used[normalized_url] = datetime.now(UTC)
        # Also update in database
        proxy_id = self.proxy_sessions[normalized_url]['proxy_id']
        proxy = Proxy.query.get(proxy_id)
        if proxy:
            proxy.last_used = self.last_used[normalized_url]
            current_app.logger.debug(f'Updated last_used time for proxy {proxy.ip}:{proxy.port} (ID: {proxy.id})')
            db.session.commit()

    def sync_states(self):
        """Sync all proxy-session pairs with database"""
        current_app.logger.info('Syncing proxy sessions with database')
        proxies = Proxy.query.all()
        for proxy in proxies:
            # Build full URL first for logging
            full_url = f"{proxy.ip}:{proxy.port}"
            if proxy.username and proxy.password:
                full_url = f"{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"

            # Get normalized URL for storage
            proxy_url = self._normalize_proxy_url(full_url)
            current_app.logger.debug(f'Processing proxy URL: {self._get_safe_proxy_url(full_url)} -> normalized: {proxy_url}')

            # Get session data if available
            session = proxy.sessions[0] if proxy.sessions else None
            session_cookie = session.session if session else None

            # Only store if valid session exists
            if session_cookie:
                current_app.logger.info(f'Found valid session for proxy {proxy_url}')
                self.proxy_sessions[proxy_url] = {
                    'session_cookie': session_cookie,
                    'proxy_id': proxy.id
                }
                self.last_used[proxy_url] = proxy.last_used or datetime.min.replace(tzinfo=UTC)
                current_app.logger.debug(f'Stored session data for {proxy_url}: {session_cookie[:10]}...')
            else:
                current_app.logger.warning(f'No valid session found for proxy {proxy_url}, skipping')

        current_app.logger.info('Proxy sessions synced with database')

    def get_next_proxy(self) -> Optional[Proxy]:
        """Get next available proxy using the proxy retriever"""
        proxy = self.proxy_retriever.get_next_proxy()
        if proxy is None:
            return None

        # Update last used time
        proxy_url = f"http://{proxy.ip}:{proxy.port}"
        self.update_last_used(proxy_url)

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
        # Get session cookie from proxy sessions
        proxy_url = f"http://{proxy.ip}:{proxy.port}"
        session_data = self.get_session(proxy_url)
        if not session_data:
            return None
        session_cookie, _ = session_data

        # Create StoryChecker
        checker = StoryChecker(
            proxy=proxy_url,
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