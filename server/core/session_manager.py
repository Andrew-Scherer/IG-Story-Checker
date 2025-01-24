"""
Session Manager
Handles proxy-session pair management
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, UTC
from models import db, Proxy
from flask import current_app

class SessionManager:
    """Manages proxy-session pairs"""

    def __init__(self):
        self.proxy_sessions: Dict[str, Dict] = {}  # proxy_url -> {session_cookie, proxy_id}
        self.last_used: Dict[str, datetime] = {}  # proxy_url -> last used time

        self.sync_states()  # Sync states with database on initialization

    def _get_safe_proxy_url(self, proxy_url: str) -> str:
        """Get proxy URL safe for logging (without credentials)"""
        # Remove protocol if present
        if '://' in proxy_url:
            proxy_url = proxy_url.split('://')[-1]
        # Remove credentials if present
        if '@' in proxy_url:
            proxy_url = proxy_url.split('@')[-1]
        return proxy_url

    def add_proxy(self, proxy_url: str, session_cookie: str) -> Optional[int]:
        """Add new proxy-session pair

        Args:
            proxy_url: Full proxy URL (e.g., http://proxy:8080)
            session_cookie: Session cookie

        Returns:
            Proxy ID if successful, None if proxy not found
        """
        current_app.logger.info(f'Adding proxy-session pair (proxy: {self._get_safe_proxy_url(proxy_url)})')

        # Get proxy ID from database
        proxy_url_no_protocol = proxy_url.split('://')[-1]  # Remove protocol
        if '@' in proxy_url_no_protocol:  # Remove auth if present
            proxy_url_no_protocol = proxy_url_no_protocol.split('@')[-1]
        ip, port = proxy_url_no_protocol.split(':')
        proxy_obj = Proxy.query.filter_by(ip=ip, port=int(port)).first()
        if not proxy_obj:
            current_app.logger.error(f'Proxy {self._get_safe_proxy_url(proxy_url)} not found in database')
            return None

        # Add to tracking
        self.proxy_sessions[proxy_url] = {
            'session_cookie': session_cookie,
            'proxy_id': proxy_obj.id
        }
        self.last_used[proxy_url] = proxy_obj.last_used or datetime.min.replace(tzinfo=UTC)

        return proxy_obj.id

    def remove_proxy(self, proxy_url: str):
        """Remove proxy-session pair"""
        current_app.logger.info(f'Removing proxy-session pair (proxy: {self._get_safe_proxy_url(proxy_url)})')
        if proxy_url in self.proxy_sessions:
            del self.proxy_sessions[proxy_url]
        if proxy_url in self.last_used:
            del self.last_used[proxy_url]

    def get_session(self, proxy_url: str) -> Optional[Tuple[str, int]]:
        """Get session cookie and proxy ID for proxy

        Returns:
            Tuple of (session_cookie, proxy_id) if found, None if not
        """
        if proxy_url not in self.proxy_sessions:
            return None
        data = self.proxy_sessions[proxy_url]
        return data['session_cookie'], data['proxy_id']

    def update_last_used(self, proxy_url: str):
        """Update last used time for proxy"""
        self.last_used[proxy_url] = datetime.now(UTC)
        # Also update in database
        proxy_id = self.proxy_sessions[proxy_url]['proxy_id']
        proxy = Proxy.query.get(proxy_id)
        if proxy:
            proxy.last_used = self.last_used[proxy_url]
            db.session.commit()

    def sync_states(self):
        """Sync all proxy-session pairs with database"""
        current_app.logger.info('Syncing proxy sessions with database')
        proxies = Proxy.query.all()
        for proxy in proxies:
            proxy_url = f"http://{proxy.ip}:{proxy.port}"
            session = proxy.sessions[0] if proxy.sessions else None
            session_cookie = session.session if session else ''
            self.proxy_sessions[proxy_url] = {
                'session_cookie': session_cookie,
                'proxy_id': proxy.id
            }
            self.last_used[proxy_url] = proxy.last_used or datetime.min.replace(tzinfo=UTC)
        current_app.logger.info('Proxy sessions synced with database')
