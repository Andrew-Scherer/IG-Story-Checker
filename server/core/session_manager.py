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
        """Normalize proxy URL format for consistent storage and retrieval.
        
        Args:
            proxy_url: Full proxy URL (e.g., http://user:pass@127.0.0.1:8080)
            
        Returns:
            Normalized URL (e.g., 127.0.0.1:8080)
        """
        # Remove protocol if present
        if '://' in proxy_url:
            proxy_url = proxy_url.split('://')[-1]
        # Remove credentials if present
        if '@' in proxy_url:
            proxy_url = proxy_url.split('@')[-1]
        return proxy_url

    def _normalize_proxy_url(self, proxy_url: str) -> str:
        """Get normalized proxy URL for storage and lookup.
        
        This is the key function that ensures consistent URL format
        across all storage and retrieval operations.
        
        Args:
            proxy_url: Full proxy URL (e.g., http://user:pass@127.0.0.1:8080)
            
        Returns:
            Normalized URL (e.g., 127.0.0.1:8080)
        """
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
                # Log all proxies for debugging
                all_proxies = Proxy.query.all()
                current_app.logger.debug(f'Available proxies: {[(p.ip, p.port) for p in all_proxies]}')
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

        # Add to tracking
        self.proxy_sessions[proxy_url] = {
            'session_cookie': session_cookie,
            'proxy_id': proxy_obj.id
        }
        self.last_used[proxy_url] = proxy_obj.last_used or datetime.min.replace(tzinfo=UTC)

        return proxy_obj.id

    def remove_proxy(self, proxy_url: str):
        """Remove proxy-session pair"""
        # Use helper for consistent URL normalization
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
        # Use helper for consistent URL normalization
        normalized_url = self._normalize_proxy_url(proxy_url)
        current_app.logger.debug(f'Looking up session for normalized proxy URL: {normalized_url}')
        
        # Try to find session with normalized URL
        session_data = self.proxy_sessions.get(normalized_url)
        if not session_data:
            current_app.logger.error(f'No session data found for proxy {normalized_url}')
            current_app.logger.debug(f'Available sessions: {list(self.proxy_sessions.keys())}')
            return None
            
        session_cookie = session_data.get('session_cookie')
        proxy_id = session_data.get('proxy_id')
        
        # Verify both session cookie and proxy ID exist
        if not session_cookie or not proxy_id:
            current_app.logger.error(f'Invalid session data for proxy {normalized_url}: missing session cookie or proxy ID')
            return None
            
        current_app.logger.info(f'Found valid session for proxy {normalized_url}')
        current_app.logger.debug(f'Session data: {session_cookie[:10]}..., proxy_id: {proxy_id}')
        return session_cookie, proxy_id

    def update_last_used(self, proxy_url: str):
        """Update last used time for proxy"""
        # Use helper for consistent URL normalization
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
