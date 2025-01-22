"""
Worker State Management
Handles individual worker state including rate limits and errors
"""

from datetime import datetime, UTC
from models.settings import SystemSettings
from flask import current_app

class WorkerState:
    """Manages state for an individual worker"""
    
    def __init__(self):
        self.error_count = 0
        self.is_disabled = False
        self.is_rate_limited = False
        self.requests_this_hour = 0
        self.hour_start = datetime.now(UTC)
        
    @property
    def max_errors(self) -> int:
        return SystemSettings.get_settings().proxy_max_failures
        
    def check_rate_limit(self) -> bool:
        """Check if worker has hit rate limit"""
        # Already rate limited
        if self.is_rate_limited:
            return True
            
        # Get settings
        settings = SystemSettings.get_settings()
        hourly_limit = settings.proxy_hourly_limit
        
        # Reset counter if hour has passed
        now = datetime.now(UTC)
        if (now - self.hour_start).total_seconds() >= 3600:
            current_app.logger.info('Resetting hourly request counter')
            self.requests_this_hour = 0
            self.hour_start = now
            self.is_rate_limited = False
            return False
            
        # Check if we've hit the limit
        if self.requests_this_hour >= hourly_limit:
            current_app.logger.warning(f'Hit hourly limit ({hourly_limit} requests)')
            self.is_rate_limited = True
            return True
            
        return False
        
    def record_success(self):
        """Record successful request"""
        self.requests_this_hour += 1
        self.error_count = 0
        
    def record_error(self, is_rate_limit: bool = False):
        """Record error"""
        self.error_count += 1
        if is_rate_limit:
            self.is_rate_limited = True
        elif self.error_count >= self.max_errors:
            current_app.logger.error(f'Exceeded max errors ({self.max_errors}), disabling')
            self.is_disabled = True
            
    def clear_rate_limit(self):
        """Clear rate limit status"""
        self.is_rate_limited = False
