"""
Worker Manager
Manages worker pool for story checking operations
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, UTC
from models.batch import BatchProfile
from core.story_checker import StoryChecker

# Set up logging
logger = logging.getLogger(__name__)

class Worker:
    """Individual worker that performs story checks"""
    
    @property
    def max_errors(self) -> int:
        """Get max errors from settings"""
        from models.settings import SystemSettings
        return SystemSettings.get_settings().proxy_max_failures
    
    def __init__(self, proxy: str, session_cookie: str, pool=None):
        """Initialize worker
        
        Args:
            proxy: Proxy to use for requests
            session_cookie: Instagram session cookie
            pool: Reference to worker pool
        """
        logger.info(f'Initializing worker with proxy {proxy}')
        self.proxy = proxy
        self.session_cookie = session_cookie
        self.story_checker = StoryChecker(proxy, session_cookie)
        self.current_profile = None
        self.last_check = None
        self.error_count = 0
        self.is_disabled = False
        self.is_rate_limited = False
        self.requests_this_hour = 0
        self.hour_start = datetime.now(UTC)
        self._pool = pool
    
    @property
    def success_rate(self) -> float:
        """Get success rate of proxy-session pair"""
        return self.story_checker.pair.success_rate
    
    @property
    def total_checks(self) -> int:
        """Get total number of checks performed"""
        return self.story_checker.pair.total_checks
    
    def check_rate_limit(self) -> bool:
        """Check if worker has hit rate limit
        
        Returns:
            True if rate limited, False otherwise
        """
        # Already rate limited
        if self.is_rate_limited:
            return True
            
        # Get settings
        from models.settings import SystemSettings
        settings = SystemSettings.get_settings()
        hourly_limit = settings.proxy_hourly_limit
        
        # Reset counter if hour has passed
        now = datetime.now(UTC)
        if (now - self.hour_start).total_seconds() >= 3600:
            logger.info(f'Resetting hourly request counter for proxy {self.proxy}')
            self.requests_this_hour = 0
            self.hour_start = now
            self.is_rate_limited = False
            # Update pool state
            if self._pool and isinstance(self._pool, WorkerPool):
                if self.proxy in self._pool.proxy_states:
                    self._pool.proxy_states[self.proxy]['rate_limited'] = False
            return False
            
        # Check if we've hit the limit
        if self.requests_this_hour >= hourly_limit:
            logger.warning(f'Proxy {self.proxy} hit hourly limit ({hourly_limit} requests)')
            self.is_rate_limited = True
            # Update pool state
            if self._pool and isinstance(self._pool, WorkerPool):
                if self.proxy in self._pool.proxy_states:
                    self._pool.proxy_states[self.proxy]['rate_limited'] = True
            return True
            
        return False

    async def check_story(self, batch_profile: BatchProfile) -> bool:
        """Check story for a profile
        
        Args:
            batch_profile: BatchProfile to check
            
        Returns:
            True if check succeeded, False if failed
        """
        if self.is_disabled:
            logger.warning(f'Worker with proxy {self.proxy} is disabled, skipping check')
            return False
            
        if self.is_rate_limited:
            logger.warning(f'Worker with proxy {self.proxy} is rate limited, skipping check')
            return False
            
        self.current_profile = batch_profile
        self.last_check = datetime.now(UTC)
        logger.info(f'Checking story for profile {batch_profile.profile.username} using proxy {self.proxy}')
        
        try:
            # Increment request counter before check
            self.requests_this_hour += 1
            
            # Check rate limit after increment
            if self.check_rate_limit():
                logger.warning(f'Worker with proxy {self.proxy} hit rate limit, skipping check')
                return False
            
            # Attempt story check
            has_story = await self.story_checker.check_profile(batch_profile.profile.username)
            
            # Update batch profile
            batch_profile.complete(has_story=has_story)
            
            # Reset error count on success
            self.error_count = 0
            logger.info(f'Successfully checked story for {batch_profile.profile.username} (has_story: {has_story})')
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f'Error checking story for {batch_profile.profile.username}: {e}', exc_info=True)
            
            # Check if error indicates rate limiting
            if "Rate limited" in str(e):
                logger.warning(f'Rate limit detected for proxy {self.proxy}')
                self.is_rate_limited = True
                # Set cooldown on proxy-session pair
                self.story_checker.pair.set_cooldown()
            
            # Disable worker if too many errors
            if self.error_count >= self.max_errors:
                logger.error(f'Worker with proxy {self.proxy} exceeded max errors ({self.max_errors}), disabling')
                self.is_disabled = True
                # Get reference to pool from worker to remove self
                if self._pool and isinstance(self._pool, WorkerPool):
                    self._pool.remove_worker(self)
            
            # Mark batch profile as failed
            batch_profile.fail(error=str(e))
            return False
        
        finally:
            self.current_profile = None
    
    def update_session(self, proxy: str, session_cookie: str) -> None:
        """Update proxy and session
        
        Args:
            proxy: New proxy to use
            session_cookie: New session cookie
        """
        logger.info(f'Updating worker session (proxy: {proxy})')
        self.proxy = proxy
        self.session_cookie = session_cookie
        self.story_checker = StoryChecker(proxy, session_cookie)
        self.error_count = 0
        self.is_disabled = False
        self.is_rate_limited = False
    
    def clear_rate_limit(self) -> None:
        """Clear rate limit status"""
        logger.info(f'Clearing rate limit for proxy {self.proxy}')
        self.is_rate_limited = False
        # Clear cooldown on proxy-session pair
        self.story_checker.pair.cooldown_until = None
        # Update pool's proxy state
        if self._pool and isinstance(self._pool, WorkerPool):
            if self.proxy in self._pool.proxy_states:
                self._pool.proxy_states[self.proxy]['rate_limited'] = False

class WorkerPool:
    """Manages pool of story checking workers"""
    
    def __init__(self):
        """Initialize worker pool"""
        from models.settings import SystemSettings
        settings = SystemSettings.get_settings()
        logger.info(f'Initializing worker pool (max_workers: {settings.max_threads})')
        self.max_workers = settings.max_threads
        self.active_workers: List[Worker] = []
        self.available_workers: List[Worker] = []
        # Track proxy-session pairs and states
        self.proxy_sessions: Dict[str, str] = {}  # proxy -> session_cookie
        self.last_used: Dict[str, datetime] = {}  # proxy -> last used time
        self.proxy_states: Dict[str, Dict] = {}  # proxy -> {disabled: bool, rate_limited: bool}
    
    def create_worker(self, proxy: str, session_cookie: str) -> Optional[Worker]:
        """Create new worker
        
        Args:
            proxy: Proxy to use
            session_cookie: Session cookie to use
            
        Returns:
            Worker instance if successful, None if initialization fails
        """
        logger.info(f'Creating new worker with proxy {proxy}')
        try:
            worker = Worker(proxy, session_cookie, pool=self)
            # Initialize proxy state if not exists
            if proxy not in self.proxy_states:
                self.proxy_states[proxy] = {'disabled': False, 'rate_limited': False}
            return worker
        except Exception as e:
            logger.error(f'Failed to create worker with proxy {proxy}: {e}')
            if proxy in self.proxy_states:
                self.proxy_states[proxy]['disabled'] = True
            return None
    
    def remove_worker(self, worker: Worker) -> None:
        """Remove worker from all pools and update proxy state
        
        Args:
            worker: Worker to remove
        """
        logger.info(f'Removing worker with proxy {worker.proxy}')
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        if worker in self.available_workers:
            self.available_workers.remove(worker)
        # Update proxy state
        if worker.proxy in self.proxy_states:
            self.proxy_states[worker.proxy]['disabled'] = worker.is_disabled
            self.proxy_states[worker.proxy]['rate_limited'] = worker.is_rate_limited
    
    def get_worker(self) -> Optional[Worker]:
        """Get available worker using round-robin rotation
        
        Returns:
            Worker if available, None if at capacity or no valid workers
        """
        # Check if we're at max capacity
        if len(self.active_workers) >= self.max_workers:
            logger.debug('Worker pool at capacity')
            return None
            
        # Get least recently used proxy
        logger.info(f'Proxy sessions: {list(self.proxy_sessions.keys())}')
        logger.info(f'Active workers: {[w.proxy for w in self.active_workers]}')
        
        # Filter out proxies that are in use, disabled, or rate-limited
        available_proxies = [
            proxy for proxy in self.proxy_sessions.keys()
            if proxy not in [w.proxy for w in self.active_workers]
            and not self.proxy_states.get(proxy, {}).get('disabled', False)
            and not self.proxy_states.get(proxy, {}).get('rate_limited', False)
        ]
        logger.info(f'Available proxies: {available_proxies}')
        
        if not available_proxies:
            logger.warning('No available proxies')
            return None
            
        # Sort by last used time (None first, then oldest to newest)
        available_proxies.sort(key=lambda p: self.last_used.get(p, datetime.min.replace(tzinfo=UTC)))
        next_proxy = available_proxies[0]
        logger.info(f'Selected proxy {next_proxy} for new worker')
        
        # Create worker with this proxy-session pair
        worker = self.create_worker(next_proxy, self.proxy_sessions[next_proxy])
        if not worker:
            logger.error(f'Failed to create worker for proxy {next_proxy}')
            return None
            
        logger.info(f'Created new worker with proxy {next_proxy} and session {self.proxy_sessions[next_proxy][:10]}...')
        
        # Remove from available and add to active
        if worker in self.available_workers:
            self.available_workers.remove(worker)
        self.active_workers.append(worker)
        logger.info(f'Added worker to active pool (active: {len(self.active_workers)}, available: {len(self.available_workers)})')
        
        return worker
    
    def release_worker(self, worker: Worker) -> None:
        """Return worker to available pool and update proxy state
        
        Args:
            worker: Worker to release
        """
        logger.info(f'Releasing worker with proxy {worker.proxy}')
        # Remove from active workers
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        # Update last used time
        self.last_used[worker.proxy] = datetime.now(UTC)
        
        # Update proxy state
        if worker.proxy in self.proxy_states:
            self.proxy_states[worker.proxy]['disabled'] = worker.is_disabled
            self.proxy_states[worker.proxy]['rate_limited'] = worker.is_rate_limited
        
        # Remove from available workers
        if worker in self.available_workers:
            self.available_workers.remove(worker)
            
        # Only add back if not disabled/rate-limited
        if not worker.is_disabled and not worker.is_rate_limited:
            self.available_workers.append(worker)
            logger.info(f'Added worker back to available pool (active: {len(self.active_workers)}, available: {len(self.available_workers)})')
        else:
            logger.info(f'Worker with proxy {worker.proxy} is disabled/rate-limited, not returning to available pool')
    
    def add_proxy_session(self, proxy: str, session_cookie: str) -> None:
        """Add new proxy-session pair to pool
        
        Args:
            proxy: Proxy URL
            session_cookie: Session cookie
        """
        logger.info(f'Adding new proxy-session pair (proxy: {proxy})')
        self.proxy_sessions[proxy] = session_cookie
        # Initialize proxy state
        self.proxy_states[proxy] = {'disabled': False, 'rate_limited': False}
    
    def remove_proxy_session(self, proxy: str, session_cookie: str) -> None:
        """Remove proxy-session pair from pool
        
        Args:
            proxy: Proxy URL
            session_cookie: Session cookie
        """
        logger.info(f'Removing proxy-session pair (proxy: {proxy})')
        if proxy in self.proxy_sessions:
            del self.proxy_sessions[proxy]
            if proxy in self.last_used:
                del self.last_used[proxy]
            if proxy in self.proxy_states:
                del self.proxy_states[proxy]
            
            # Remove any workers using this proxy
            for worker in list(self.active_workers):
                if worker.proxy == proxy:
                    self.remove_worker(worker)
            for worker in list(self.available_workers):
                if worker.proxy == proxy:
                    self.remove_worker(worker)
