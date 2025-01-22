"""
Proxy Session Management
Handles proxy-session pairs and their states
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, UTC
from statistics import mean
from models import db, Proxy
from flask import current_app

class ProxyManager:
    """Manages proxy-session pairs and their states"""
    
    def __init__(self):
        self.proxy_sessions: Dict[str, Dict] = {}  # proxy -> {session_cookie, proxy_id}
        self.last_used: Dict[str, datetime] = {}  # proxy -> last used time
        self.states: Dict[str, Dict] = {}  # proxy -> {disabled: bool, rate_limited: bool}
        
        # Metrics
        self.usage_count: Dict[str, int] = {}  # proxy -> number of times used
        self.success_count: Dict[str, int] = {}  # proxy -> number of successful requests
        self.response_times: Dict[str, list] = {}  # proxy -> list of response times
        self.rate_limit_count: Dict[str, int] = {}  # proxy -> number of rate limits encountered
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
        
    def add_proxy(self, proxy_url: str, session_cookie: str) -> Optional[str]:
        """Add new proxy-session pair
        
        Args:
            proxy_url: Full proxy URL (e.g. http://proxy:8080)
            session_cookie: Session cookie
            
        Returns:
            Proxy ID if successful, None if proxy not found
        """
        current_app.logger.info(f'Adding proxy-session pair (proxy: {self._get_safe_proxy_url(proxy_url)})')
        
        # Get proxy ID from database
        proxy_url = proxy_url.split('://')[-1]  # Remove protocol
        if '@' in proxy_url:  # Remove auth if present
            proxy_url = proxy_url.split('@')[-1]
        ip, port = proxy_url.split(':')
        proxy_obj = Proxy.query.filter_by(ip=ip, port=int(port)).first()
        if not proxy_obj:
            current_app.logger.error(f'Proxy {self._get_safe_proxy_url(proxy_url)} not found in database')
            return None
            
        # Add to tracking
        self.proxy_sessions[proxy_url] = {
            'session_cookie': session_cookie,
            'proxy_id': proxy_obj.id
        }
        self.states[proxy_url] = {
            'disabled': False,
            'rate_limited': False
        }
        
        return proxy_obj.id
        
    def remove_proxy(self, proxy_url: str):
        """Remove proxy-session pair"""
        current_app.logger.info(f'Removing proxy-session pair (proxy: {self._get_safe_proxy_url(proxy_url)})')
        if proxy_url in self.proxy_sessions:
            del self.proxy_sessions[proxy_url]
        if proxy_url in self.last_used:
            del self.last_used[proxy_url]
        if proxy_url in self.states:
            del self.states[proxy_url]
            
    def get_session(self, proxy_url: str) -> Optional[Tuple[str, str]]:
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
        
    def get_available_proxy(self, cooldown_seconds: int) -> Optional[str]:
        """Get available proxy that hasn't been used in cooldown_seconds
        
        Args:
            cooldown_seconds: Minimum seconds since last use
            
        Returns:
            Proxy URL if available, None if no proxies ready
        """
        now = datetime.now(UTC)
        available = []
        
        for proxy in self.proxy_sessions.keys():
            # Skip disabled or rate-limited proxies
            if self.states[proxy]['disabled'] or self.states[proxy]['rate_limited']:
                continue
                
            # Get time since last use (default to epoch if never used)
            last_used = self.last_used.get(proxy, datetime.min.replace(tzinfo=UTC))
            elapsed = (now - last_used).total_seconds()
            
            if elapsed >= cooldown_seconds:
                available.append((proxy, last_used))
        
        if not available:
            return None
            
        # Return least recently used proxy that meets cooldown
        available.sort(key=lambda x: x[1])
        return available[0][0]
        
    def update_state(self, proxy_url: str, disabled: bool = None, rate_limited: bool = None):
        """Update proxy state"""
        if proxy_url in self.states:
            if disabled is not None:
                self.states[proxy_url]['disabled'] = disabled
            if rate_limited is not None:
                self.states[proxy_url]['rate_limited'] = rate_limited
            
            # Update database
            proxy_id = self.proxy_sessions[proxy_url]['proxy_id']
            proxy = Proxy.query.get(proxy_id)
            if proxy:
                if disabled is not None:
                    proxy.disabled = disabled
                if rate_limited is not None:
                    proxy.rate_limited = rate_limited
                db.session.commit()
                current_app.logger.info(f'Updated state for proxy {self._get_safe_proxy_url(proxy_url)} in database')
            else:
                current_app.logger.error(f'Proxy {self._get_safe_proxy_url(proxy_url)} not found in database')

    def sync_states(self):
        """Sync all proxy states with database"""
        current_app.logger.info('Syncing proxy states with database')
        for proxy_url, data in self.proxy_sessions.items():
            proxy_id = data['proxy_id']
            proxy = Proxy.query.get(proxy_id)
            if proxy:
                self.states[proxy_url] = {
            'disabled': not proxy.is_active,
                    'rate_limited': proxy.rate_limited
                }
                self.last_used[proxy_url] = proxy.last_used or datetime.min.replace(tzinfo=UTC)
            else:
                current_app.logger.error(f'Proxy {self._get_safe_proxy_url(proxy_url)} not found in database')
        current_app.logger.info('Proxy states synced with database')

    def get_proxy_state(self, proxy_url: str) -> Dict[str, bool]:
        """Get current state of a proxy"""
        return self.states.get(proxy_url, {'disabled': False, 'rate_limited': False})

    def record_proxy_usage(self, proxy_url: str):
        """Record usage of a proxy"""
        self.usage_count[proxy_url] = self.usage_count.get(proxy_url, 0) + 1

    def record_proxy_success(self, proxy_url: str):
        """Record successful use of a proxy"""
        self.success_count[proxy_url] = self.success_count.get(proxy_url, 0) + 1

    def record_response_time(self, proxy_url: str, response_time: float):
        """Record response time for a proxy"""
        if proxy_url not in self.response_times:
            self.response_times[proxy_url] = []
        self.response_times[proxy_url].append(response_time)

    def record_rate_limit(self, proxy_url: str):
        """Record rate limit encounter for a proxy"""
        self.rate_limit_count[proxy_url] = self.rate_limit_count.get(proxy_url, 0) + 1

    def get_proxy_metrics(self, proxy_url: str) -> Dict[str, float]:
        """Get metrics for a specific proxy"""
        usage = self.usage_count.get(proxy_url, 0)
        success = self.success_count.get(proxy_url, 0)
        avg_response_time = mean(self.response_times.get(proxy_url, [0]))
        rate_limits = self.rate_limit_count.get(proxy_url, 0)

        success_rate = (success / usage) * 100 if usage > 0 else 0

        return {
            'usage_count': usage,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'rate_limit_count': rate_limits
        }

    def get_all_proxy_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get metrics for all proxies"""
        return {proxy: self.get_proxy_metrics(proxy) for proxy in self.proxy_sessions.keys()}
