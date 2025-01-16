"""
Tests for worker health metrics tracking and reporting
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch
from core.worker_health import WorkerHealth, HealthStatus
from core.worker_manager import Worker

@pytest.fixture
def mock_worker():
    worker = Mock(spec=Worker)
    worker.proxy = "192.168.1.1:8080"
    worker.session_cookie = "test_session"
    worker.requests_this_hour = 0
    worker.hour_start = datetime.now(UTC)
    worker.is_rate_limited = False
    worker.is_disabled = False
    worker.error_count = 0
    return worker

@pytest.fixture
def health_tracker():
    return WorkerHealth()

def test_rate_limit_tracking(health_tracker, mock_worker):
    """Test rate limit tracking for proxy-session pairs"""
    
    # Should start with no requests
    assert health_tracker.get_requests_this_hour(mock_worker) == 0
    
    # Add some requests
    for _ in range(50):
        health_tracker.record_request(mock_worker)
    
    assert health_tracker.get_requests_this_hour(mock_worker) == 50
    assert not health_tracker.is_rate_limited(mock_worker)
    
    # Add requests up to limit
    for _ in range(100):
        health_tracker.record_request(mock_worker)
    
    assert health_tracker.get_requests_this_hour(mock_worker) == 150
    assert health_tracker.is_rate_limited(mock_worker)
    
    # Should reject additional requests
    with pytest.raises(Exception) as exc:
        health_tracker.record_request(mock_worker)
    assert "Rate limit exceeded" in str(exc.value)

def test_rate_limit_reset(health_tracker, mock_worker):
    """Test rate limit counter reset after an hour"""
    
    # Start in hour 1
    mock_now = datetime(2024, 1, 1, 1, 0, 0, tzinfo=UTC)
    with patch('core.worker_health.datetime') as mock_dt:
        mock_dt.now.return_value = mock_now
        mock_dt.UTC = UTC
        
        # Add some requests in hour 1
        for _ in range(50):
            health_tracker.record_request(mock_worker)
            
        # Move to hour 2
        mock_now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=UTC)
        mock_dt.now.return_value = mock_now
        
        # Should reset counter
        assert health_tracker.get_requests_this_hour(mock_worker) == 0

def test_success_rate_tracking(health_tracker, mock_worker):
    """Test success rate calculation"""
    
    # Record mix of successes and failures
    health_tracker.record_success(mock_worker)
    health_tracker.record_success(mock_worker)
    health_tracker.record_failure(mock_worker)
    health_tracker.record_success(mock_worker)
    
    assert health_tracker.get_success_rate(mock_worker) == 0.75

def test_response_time_tracking(health_tracker, mock_worker):
    """Test response time monitoring"""
    
    # Record some response times
    health_tracker.record_response_time(mock_worker, 100)  # 100ms
    health_tracker.record_response_time(mock_worker, 200)  # 200ms
    health_tracker.record_response_time(mock_worker, 150)  # 150ms
    
    assert 145 <= health_tracker.get_average_response_time(mock_worker) <= 155

def test_health_status_reporting(health_tracker, mock_worker):
    """Test overall health status determination"""
    
    # Should start as healthy (no requests yet)
    assert health_tracker.get_status(mock_worker) == HealthStatus.HEALTHY
    
    # Record some requests to meet minimum threshold
    for _ in range(5):
        health_tracker.record_request(mock_worker)
        health_tracker.record_failure(mock_worker)
    
    # Should be degraded with 0% success rate
    assert health_tracker.get_status(mock_worker) == HealthStatus.DEGRADED
    
    # Add more failures to reach failing threshold
    for _ in range(5):
        health_tracker.record_request(mock_worker)
        health_tracker.record_failure(mock_worker)
    
    # Should be failing with 0% success rate and >= 10 requests
    assert health_tracker.get_status(mock_worker) == HealthStatus.FAILING
    
    # Record successes to improve health
    for _ in range(20):
        health_tracker.record_request(mock_worker)
        health_tracker.record_success(mock_worker)
    
    # Should be healthy with high success rate
    assert health_tracker.get_status(mock_worker) == HealthStatus.HEALTHY

def test_statistics_aggregation(health_tracker, mock_worker):
    """Test aggregation of health metrics"""
    
    # Record various metrics
    health_tracker.record_request(mock_worker)
    health_tracker.record_success(mock_worker)
    health_tracker.record_response_time(mock_worker, 150)
    
    stats = health_tracker.get_statistics(mock_worker)
    
    assert stats["requests_this_hour"] == 1
    assert stats["success_rate"] == 1.0
    assert stats["avg_response_time"] == 150
    assert stats["status"] == HealthStatus.HEALTHY
    assert not stats["is_rate_limited"]

def test_multiple_workers(health_tracker):
    """Test tracking multiple workers independently"""
    
    worker1 = Mock(spec=Worker)
    worker1.proxy = "192.168.1.1:8080"
    worker1.session_cookie = "session1"
    worker1.hour_start = datetime.now(UTC)
    
    worker2 = Mock(spec=Worker)
    worker2.proxy = "192.168.1.2:8080"
    worker2.session_cookie = "session2"
    worker2.hour_start = datetime.now(UTC)
    
    # Record metrics for both workers
    health_tracker.record_request(worker1)
    health_tracker.record_success(worker1)
    
    health_tracker.record_request(worker2)
    health_tracker.record_failure(worker2)
    
    # Should track stats independently
    assert health_tracker.get_success_rate(worker1) == 1.0
    assert health_tracker.get_success_rate(worker2) == 0.0
