"""
Worker Manager
Manages worker pool for story checking operations
"""

from typing import Optional, List, Set, Dict, Tuple
from datetime import datetime, UTC
from models.batch import BatchProfile
from core.story_checker import StoryChecker, ProxySessionPair

class Worker:
    """Individual worker that performs story checks"""
    
    MAX_ERRORS = 3  # Maximum errors before worker is disabled
    
    def __init__(self, proxy: str, session_cookie: str):
        """Initialize worker
        
        Args:
            proxy: Proxy to use for requests
            session_cookie: Instagram session cookie
        """
        self.proxy = proxy
        self.session_cookie = session_cookie
        self.story_checker = StoryChecker(proxy, session_cookie)
        self.current_profile = None
        self.last_check = None
        self.error_count = 0
        self.is_disabled = False
        self.is_rate_limited = False
    
    @property
    def success_rate(self) -> float:
        """Get success rate of proxy-session pair"""
        return self.story_checker.pair.success_rate
    
    @property
    def total_checks(self) -> int:
        """Get total number of checks performed"""
        return self.story_checker.pair.total_checks
    
    async def check_story(self, batch_profile: BatchProfile) -> bool:
        """Check story for a profile
        
        Args:
            batch_profile: BatchProfile to check
            
        Returns:
            True if check succeeded, False if failed
        """
        if self.is_disabled or self.is_rate_limited:
            return False
            
        self.current_profile = batch_profile
        self.last_check = datetime.now(UTC)
        
        try:
            # Attempt story check
            has_story = await self.story_checker.check_profile(batch_profile.profile.username)
            
            # Update batch profile
            batch_profile.complete(has_story=has_story)
            
            # Reset error count on success
            self.error_count = 0
            return True
            
        except Exception as e:
            self.error_count += 1
            
            # Check if error indicates rate limiting
            if "Rate limited" in str(e):
                self.is_rate_limited = True
                # Set cooldown on proxy-session pair
                self.story_checker.pair.set_cooldown()
            
            # Disable worker if too many errors
            if self.error_count >= self.MAX_ERRORS:
                self.is_disabled = True
                # Get reference to pool from worker to remove self
                pool = getattr(self, '_pool', None)
                if pool and isinstance(pool, WorkerPool):
                    pool.remove_worker(self)
            
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
        self.proxy = proxy
        self.session_cookie = session_cookie
        self.story_checker = StoryChecker(proxy, session_cookie)
        self.error_count = 0
        self.is_disabled = False
        self.is_rate_limited = False
    
    def clear_rate_limit(self) -> None:
        """Clear rate limit status"""
        self.is_rate_limited = False
        # Clear cooldown on proxy-session pair
        self.story_checker.pair.cooldown_until = None

class WorkerPool:
    """Manages pool of story checking workers"""
    
    def __init__(self, max_workers: int = 2):
        """Initialize worker pool
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.active_workers: List[Worker] = []
        self.available_workers: List[Worker] = []
        # Track proxy-session pairs and their performance
        self.proxy_sessions: Dict[str, List[Tuple[str, str]]] = {}  # proxy -> [(session, success_rate)]
    
    def create_worker(self, proxy: str, session_cookie: str) -> Worker:
        """Create new worker
        
        Args:
            proxy: Proxy to use
            session_cookie: Session cookie to use
            
        Returns:
            New worker instance
        """
        worker = Worker(proxy, session_cookie)
        # Store reference to pool in worker
        worker._pool = self
        return worker
    
    def remove_worker(self, worker: Worker) -> None:
        """Remove worker from all pools
        
        Args:
            worker: Worker to remove
        """
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        if worker in self.available_workers:
            self.available_workers.remove(worker)
    
    def get_worker(self) -> Optional[Worker]:
        """Get available worker
        
        Returns:
            Worker if available, None if at capacity
        """
        # Check if we're at max capacity
        if len(self.active_workers) >= self.max_workers:
            return None
        
        # Get best performing proxy-session pair
        best_proxy = None
        best_session = None
        best_rate = 0.0
        
        for proxy, sessions in self.proxy_sessions.items():
            for session, rate in sessions:
                if rate > best_rate:
                    best_proxy = proxy
                    best_session = session
                    best_rate = rate
        
        if not best_proxy or not best_session:
            return None
            
        # Create worker with best pair
        worker = self.create_worker(best_proxy, best_session)
        
        # Remove from available and add to active
        if worker in self.available_workers:
            self.available_workers.remove(worker)
        self.active_workers.append(worker)
        
        return worker
    
    def release_worker(self, worker: Worker) -> None:
        """Return worker to available pool
        
        Args:
            worker: Worker to release
        """
        # Remove from active workers
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        # Update proxy-session performance metrics
        if worker.proxy in self.proxy_sessions:
            sessions = self.proxy_sessions[worker.proxy]
            # Update success rate for this session
            for i, (session, _) in enumerate(sessions):
                if session == worker.session_cookie:
                    sessions[i] = (session, worker.success_rate)
                    break
        
        # Clear from available workers if disabled or rate limited
        if worker.is_disabled or worker.is_rate_limited:
            if worker in self.available_workers:
                self.available_workers.remove(worker)
        else:
            # Only add to available if not already there
            if worker not in self.available_workers:
                self.available_workers.append(worker)
    
    def add_proxy_session(self, proxy: str, session_cookie: str) -> None:
        """Add new proxy-session pair to pool
        
        Args:
            proxy: Proxy URL
            session_cookie: Session cookie
        """
        if proxy not in self.proxy_sessions:
            self.proxy_sessions[proxy] = []
        # Add with initial 100% success rate
        self.proxy_sessions[proxy].append((session_cookie, 1.0))
    
    def remove_proxy_session(self, proxy: str, session_cookie: str) -> None:
        """Remove proxy-session pair from pool
        
        Args:
            proxy: Proxy URL
            session_cookie: Session cookie
        """
        if proxy in self.proxy_sessions:
            self.proxy_sessions[proxy] = [
                (session, rate) for session, rate in self.proxy_sessions[proxy]
                if session != session_cookie
            ]
            if not self.proxy_sessions[proxy]:
                del self.proxy_sessions[proxy]
