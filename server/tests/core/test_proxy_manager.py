"""
Test Proxy Manager
Tests proxy pool management and rotation strategies
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch
from models.proxy import Proxy, ProxyStatus
from models.session import Session
from core.story_checker import StoryChecker

from core.proxy_manager import ProxyManager

@pytest.fixture
def db_session():
    """Create mock database session"""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.query = Mock()
    return session

@pytest.fixture
def proxy_manager(db_session):
    """Create proxy manager for testing"""
    manager = ProxyManager(db_session)
    return manager

@pytest.fixture
def sample_proxies(db_session):
    """Create sample proxies for testing"""
    proxies = []
    for i in range(3):
        proxy = Proxy(
            ip=f"192.168.1.{i+1}",
            port=8080 + i,
            username=f"user{i+1}",
            password=f"pass{i+1}",
            # Initialize tracking fields
            total_requests=0,
            failed_requests=0,
            requests_this_hour=0,
            error_count=0,
            status=ProxyStatus.ACTIVE
        )
        proxies.append(proxy)
    
    # Set up mock query behavior
    def mock_filter(*args):
        # Filter proxies based on status and cooldown
        filtered = [p for p in proxies if p.status == ProxyStatus.ACTIVE]
        mock_result = Mock()
        mock_result.all.return_value = filtered
        return mock_result
    
    db_session.query.return_value.filter = mock_filter
    db_session.query.return_value.all.return_value = proxies
    
    return proxies

def test_get_available_proxies(proxy_manager, sample_proxies, db_session):
    """Test getting available proxies"""
    # All proxies start as active
    proxies = proxy_manager.get_available_proxies()
    assert len(proxies) == 3
    
    # Mark one proxy as disabled
    sample_proxies[0].status = ProxyStatus.DISABLED
    proxies = proxy_manager.get_available_proxies()
    assert len(proxies) == 2
    assert sample_proxies[0] not in proxies
    
    # Mark another as rate limited
    sample_proxies[1].status = ProxyStatus.RATE_LIMITED
    sample_proxies[1].cooldown_until = datetime.now(UTC) + timedelta(minutes=15)
    proxies = proxy_manager.get_available_proxies()
    assert len(proxies) == 1
    assert proxies[0] == sample_proxies[2]

def test_proxy_rotation(proxy_manager, sample_proxies):
    """Test proxy rotation strategy"""
    # First call should get least used proxy
    proxy1 = proxy_manager.get_next_proxy()
    assert proxy1.total_requests == 0
    
    # Record some usage
    proxy1.total_requests = 10
    proxy1.last_used = datetime.now(UTC)
    
    # Next call should get different proxy
    proxy2 = proxy_manager.get_next_proxy()
    assert proxy2 != proxy1
    assert proxy2.total_requests == 0

def test_proxy_health_check(proxy_manager, sample_proxies):
    """Test proxy health monitoring"""
    proxy = sample_proxies[0]
    
    # Start with healthy proxy
    assert proxy_manager.is_proxy_healthy(proxy) is True
    
    # Record some errors
    proxy.error_count = proxy_manager.ERROR_THRESHOLD - 1
    assert proxy_manager.is_proxy_healthy(proxy) is True
    
    # One more error should mark as unhealthy
    proxy.error_count = proxy_manager.ERROR_THRESHOLD
    assert proxy_manager.is_proxy_healthy(proxy) is False

def test_rate_limit_handling(proxy_manager, sample_proxies):
    """Test rate limit detection and handling"""
    proxy = sample_proxies[0]
    
    # Record requests up to limit
    for _ in range(proxy_manager.HOURLY_LIMIT):
        proxy_manager.record_request(proxy, success=True)
    
    assert proxy.status == ProxyStatus.RATE_LIMITED
    assert proxy.cooldown_until > datetime.now(UTC)
    
    # Should not be available during cooldown
    assert proxy not in proxy_manager.get_available_proxies()
    
    # After cooldown expires
    proxy.cooldown_until = datetime.now(UTC) - timedelta(minutes=1)
    assert proxy in proxy_manager.get_available_proxies()
    assert proxy.status == ProxyStatus.ACTIVE

def test_proxy_cleanup(proxy_manager, sample_proxies):
    """Test removing unhealthy proxies"""
    # Mark proxies as unhealthy
    sample_proxies[0].error_count = proxy_manager.ERROR_THRESHOLD
    sample_proxies[1].status = ProxyStatus.DISABLED
    
    # Clean up should mark unhealthy proxies as disabled
    proxy_manager.cleanup_proxies()
    
    # Check statuses
    assert sample_proxies[0].status == ProxyStatus.DISABLED
    assert sample_proxies[1].status == ProxyStatus.DISABLED
    assert sample_proxies[2].status == ProxyStatus.ACTIVE
    
    # Only active proxies should be available
    available = proxy_manager.get_available_proxies()
    assert len(available) == 1
    assert available[0] == sample_proxies[2]

def test_story_checker_integration(proxy_manager, sample_proxies):
    """Test integration with StoryChecker"""
    proxy = sample_proxies[0]
    session = Session(session="test_session_123")
    proxy.sessions.append(session)
    
    # Create story checker
    checker = proxy_manager.create_story_checker(proxy)
    assert isinstance(checker, StoryChecker)
    # Should use base URL without credentials
    expected_url = f"http://{proxy.ip}:{proxy.port}"
    assert checker.pair.proxy == expected_url
    assert checker.pair.session_cookie == session.session

def test_load_balancing(proxy_manager, sample_proxies):
    """Test load balancing between proxies"""
    # Record different usage levels
    sample_proxies[0].total_requests = 100
    sample_proxies[1].total_requests = 50
    sample_proxies[2].total_requests = 10
    
    # Should prefer least used proxy
    next_proxy = proxy_manager.get_next_proxy()
    assert next_proxy == sample_proxies[2]
    
    # After using least used, should get next least used
    next_proxy.total_requests = 100  # Make it most used
    proxy_manager.db.commit()  # Commit changes to database
    
    # Now should get proxy with 50 requests
    next_proxy = proxy_manager.get_next_proxy()
    assert next_proxy == sample_proxies[1]  # Has 50 requests

def test_proxy_metrics(proxy_manager, sample_proxies):
    """Test proxy performance metrics"""
    proxy = sample_proxies[0]
    
    # Record mix of successes and failures
    proxy_manager.record_request(proxy, success=True, response_time=100)
    proxy_manager.record_request(proxy, success=True, response_time=150)
    proxy_manager.record_request(proxy, success=False, error="Timeout")
    
    metrics = proxy_manager.get_proxy_metrics(proxy)
    assert metrics['success_rate'] == 2/3
    assert 100 <= metrics['avg_response_time'] <= 150
    assert metrics['total_requests'] == 3
    assert metrics['error_count'] == 1
