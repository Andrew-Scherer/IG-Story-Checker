"""
Worker health metrics tracking and reporting
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Dict, Any

class HealthStatus(Enum):
    """Worker health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"

class WorkerHealth:
    """Tracks health metrics for worker proxy-session pairs"""
    
    # Constants for health status thresholds
    DEGRADED_THRESHOLD = 0.8  # Success rate below 80% is degraded
    FAILING_THRESHOLD = 0.5   # Success rate below 50% is failing
    REQUEST_LIMIT = 150       # Maximum requests per hour
    
    def __init__(self):
        """Initialize health tracker"""
        self._requests: Dict[str, int] = {}
        self._successes: Dict[str, int] = {}
        self._failures: Dict[str, int] = {}
        self._response_times: Dict[str, list] = {}
        self._current_hour = datetime.now(UTC).hour
    
    def _get_worker_key(self, worker) -> str:
        """Get unique key for worker"""
        return f"{worker.proxy}:{worker.session_cookie}"
    
    def _check_new_hour(self) -> bool:
        """Check if we've entered a new hour"""
        current_hour = datetime.now(UTC).hour
        if current_hour != self._current_hour:
            self._requests = {}
            self._successes = {}
            self._failures = {}
            self._response_times = {}
            self._current_hour = current_hour
            return True
        return False
    
    def get_requests_this_hour(self, worker) -> int:
        """Get number of requests made this hour"""
        self._check_new_hour()
        key = self._get_worker_key(worker)
        return self._requests.get(key, 0)
    
    def record_request(self, worker) -> None:
        """Record a request for a worker
        
        Args:
            worker: Worker instance making request
            
        Raises:
            Exception: If rate limit exceeded
        """
        self._check_new_hour()
        key = self._get_worker_key(worker)
        
        if self._requests.get(key, 0) >= self.REQUEST_LIMIT:
            raise Exception("Rate limit exceeded for proxy-session pair")
            
        self._requests[key] = self._requests.get(key, 0) + 1
    
    def record_success(self, worker) -> None:
        """Record a successful request"""
        key = self._get_worker_key(worker)
        self._successes[key] = self._successes.get(key, 0) + 1
    
    def record_failure(self, worker) -> None:
        """Record a failed request"""
        key = self._get_worker_key(worker)
        self._failures[key] = self._failures.get(key, 0) + 1
    
    def record_response_time(self, worker, time_ms: int) -> None:
        """Record response time in milliseconds"""
        key = self._get_worker_key(worker)
        if key not in self._response_times:
            self._response_times[key] = []
        self._response_times[key].append(time_ms)
        
        # Keep only last 100 response times
        if len(self._response_times[key]) > 100:
            self._response_times[key].pop(0)
    
    def get_hour_start(self, worker) -> datetime:
        """Get start time of current hour window"""
        now = datetime.now(UTC)
        return now.replace(minute=0, second=0, microsecond=0)
    
    def is_rate_limited(self, worker) -> bool:
        """Check if worker is currently rate limited"""
        return self.get_requests_this_hour(worker) >= self.REQUEST_LIMIT
    
    def get_success_rate(self, worker) -> float:
        """Get success rate for worker"""
        key = self._get_worker_key(worker)
        successes = self._successes.get(key, 0)
        failures = self._failures.get(key, 0)
        total = successes + failures
        return successes / total if total > 0 else 1.0
    
    def get_average_response_time(self, worker) -> float:
        """Get average response time in milliseconds"""
        key = self._get_worker_key(worker)
        times = self._response_times.get(key, [])
        return sum(times) / len(times) if times else None
    
    def get_status(self, worker) -> HealthStatus:
        """Get overall health status"""
        key = self._get_worker_key(worker)
        successes = self._successes.get(key, 0)
        failures = self._failures.get(key, 0)
        total = successes + failures
        
        # Need at least 5 requests to determine status
        if total < 5:
            return HealthStatus.HEALTHY
            
        success_rate = successes / total if total > 0 else 1.0
        
        # Calculate recent success rate (last 20 requests)
        recent_total = min(total, 20)
        recent_success_rate = successes / recent_total if recent_total > 0 else 1.0
        
        # Need at least 10 requests for failing status
        if success_rate < self.FAILING_THRESHOLD and total >= 10:
            return HealthStatus.FAILING
        # Consider recent success rate for health status
        elif recent_success_rate >= self.DEGRADED_THRESHOLD and successes >= 10:
            return HealthStatus.HEALTHY
        elif success_rate < self.DEGRADED_THRESHOLD and total >= 5:
            return HealthStatus.DEGRADED
        # Default to healthy if we don't have enough data
        return HealthStatus.HEALTHY
    
    def get_statistics(self, worker) -> Dict[str, Any]:
        """Get all health statistics for worker"""
        return {
            "requests_this_hour": self.get_requests_this_hour(worker),
            "success_rate": self.get_success_rate(worker),
            "avg_response_time": self.get_average_response_time(worker),
            "status": self.get_status(worker),
            "is_rate_limited": self.is_rate_limited(worker)
        }
