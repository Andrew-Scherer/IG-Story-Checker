"""
Test Worker Manager
Tests worker pool management and proxy validation
"""

import pytest
pytestmark = pytest.mark.asyncio
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch, AsyncMock
from models.batch import BatchProfile
from core.worker_manager import WorkerPool, Worker

@pytest.fixture
def mock_settings():
    """Mock system settings"""
    with patch('models.settings.SystemSettings') as mock:
        settings = Mock()
        settings.max_threads = 2
        settings.proxy_max_failures = 3
        settings.proxy_hourly_limit = 50
        mock.get_settings.return_value = settings
        yield settings

@pytest.fixture
def worker_pool(mock_settings):
    """Create worker pool for testing"""
    return WorkerPool()

@pytest.fixture
def mock_story_checker():
    """Create mock story checker"""
    with patch('core.worker_manager.StoryChecker') as mock:
        checker = Mock()
        mock.return_value = checker
        checker.check_profile = AsyncMock(return_value=True)
        checker.validate_proxy = AsyncMock(return_value=True)
        checker.pair = Mock()
        checker.pair.success_rate = 1.0
        checker.pair.total_checks = 0
        checker.pair.set_cooldown = Mock()
        yield checker

async def test_proxy_validation(worker_pool, mock_story_checker, create_proxy_session):
    """Test proxy validation before use"""
    # Create proxy-session pair
    proxy, session = create_proxy_session()
    worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)

    # Test successful validation
    mock_story_checker.validate_proxy.return_value = True
    worker = worker_pool.get_worker()
    assert worker is not None
    assert worker.proxy == f"http://{proxy.ip}:{proxy.port}"
    assert worker.session_cookie == session.session

    # Test failed validation
    mock_story_checker.validate_proxy.return_value = False
    worker.is_disabled = True
    worker_pool.release_worker(worker)
    worker = worker_pool.get_worker()
    assert worker is None

async def test_proxy_reuse(worker_pool, mock_story_checker, create_proxy_session, create_batch_profile):
    """Test proxy reuse after successful check"""
    # Create proxy and batch profile
    proxy, session = create_proxy_session()
    batch_profile = create_batch_profile()
    worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)

    # Get worker and use it
    worker = worker_pool.get_worker()
    assert worker is not None
    
    success = await worker.check_story(batch_profile)
    assert success is True
    
    worker_pool.release_worker(worker)

    # Should be able to reuse the worker
    worker2 = worker_pool.get_worker()
    assert worker2 is not None
    assert worker2.proxy == worker.proxy

async def test_rate_limit_handling(worker_pool, mock_story_checker, create_proxy_session, create_batch_profile):
    """Test handling of rate limited proxies"""
    # Create two proxy-session pairs
    proxy1, session1 = create_proxy_session('http://proxy1:8080')
    proxy2, session2 = create_proxy_session('http://proxy2:8080')
    worker_pool.add_proxy_session(f"http://{proxy1.ip}:{proxy1.port}", session1.session)
    worker_pool.add_proxy_session(f"http://{proxy2.ip}:{proxy2.port}", session2.session)

    batch_profile = create_batch_profile()

    # First worker gets rate limited
    worker1 = worker_pool.get_worker()
    mock_story_checker.check_profile.side_effect = Exception("Rate limited")
    success = await worker1.check_story(batch_profile)
    assert success is False
    assert worker1.is_rate_limited
    worker_pool.release_worker(worker1)

    # Should get second worker
    mock_story_checker.check_profile.side_effect = None
    worker2 = worker_pool.get_worker()
    assert worker2 is not None
    assert worker2.proxy != worker1.proxy
    
    success = await worker2.check_story(batch_profile)
    assert success is True

async def test_proxy_error_threshold(worker_pool, mock_story_checker, mock_settings, create_proxy_session, create_batch_profile):
    """Test handling of failing proxies"""
    proxy, session = create_proxy_session()
    worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)
    batch_profile = create_batch_profile()

    # Simulate repeated errors
    mock_story_checker.check_profile.side_effect = Exception("Connection error")
    worker = worker_pool.get_worker()
    
    for _ in range(mock_settings.proxy_max_failures):
        success = await worker.check_story(batch_profile)
        assert success is False
    
    # Worker should be disabled after max errors
    assert worker.is_disabled
    worker_pool.release_worker(worker)
    
    # Should not get disabled worker
    next_worker = worker_pool.get_worker()
    assert next_worker is None

async def test_proxy_cooldown(worker_pool, mock_story_checker, create_proxy_session):
    """Test proxy cooldown after rate limit"""
    proxy, session = create_proxy_session()
    worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)

    # Get worker and trigger rate limit
    worker = worker_pool.get_worker()
    worker.is_rate_limited = True
    worker_pool.release_worker(worker)

    # Should not get worker during cooldown
    next_worker = worker_pool.get_worker()
    assert next_worker is None

    # After clearing rate limit
    worker.clear_rate_limit()
    next_worker = worker_pool.get_worker()
    assert next_worker is not None

async def test_concurrent_workers(worker_pool, mock_story_checker, create_proxy_session):
    """Test concurrent worker limits"""
    # Add max_threads + 1 proxies
    proxies = []
    for i in range(worker_pool.max_workers + 1):
        proxy, session = create_proxy_session(f'http://proxy{i}:8080')
        worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)
        proxies.append(proxy)

    # Should get max_threads workers
    workers = []
    for _ in range(worker_pool.max_workers):
        worker = worker_pool.get_worker()
        assert worker is not None
        workers.append(worker)

    # Should not get another worker
    worker = worker_pool.get_worker()
    assert worker is None

    # Release one worker
    worker_pool.release_worker(workers[0])

    # Should now get another worker
    worker = worker_pool.get_worker()
    assert worker is not None

async def test_hourly_rate_limit(worker_pool, mock_story_checker, mock_settings, create_proxy_session, create_batch_profile):
    """Test hourly rate limit handling"""
    proxy, session = create_proxy_session()
    worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)
    batch_profile = create_batch_profile()

    # Get worker
    worker = worker_pool.get_worker()
    assert worker is not None

    # Do max hourly requests - 1
    for _ in range(mock_settings.proxy_hourly_limit - 1):
        success = await worker.check_story(batch_profile)
        assert success is True
        assert worker.check_rate_limit() is False

    # One more request should hit the limit
    success = await worker.check_story(batch_profile)
    assert success is False
    assert worker.is_rate_limited is True

    # Move clock forward an hour and clear rate limit
    worker.hour_start = datetime.now(UTC) - timedelta(hours=1, minutes=1)
    worker.clear_rate_limit()

    # Should be able to make requests again
    assert worker.is_rate_limited is False
    success = await worker.check_story(batch_profile)
    assert success is True

async def test_least_recently_used(worker_pool, mock_story_checker, create_proxy_session):
    """Test least recently used proxy selection"""
    # Create three proxies
    proxy1, session1 = create_proxy_session('http://proxy1:8080')
    proxy2, session2 = create_proxy_session('http://proxy2:8080')
    proxy3, session3 = create_proxy_session('http://proxy3:8080')

    # Add them in order
    worker_pool.add_proxy_session(f"http://{proxy1.ip}:{proxy1.port}", session1.session)
    worker_pool.add_proxy_session(f"http://{proxy2.ip}:{proxy2.port}", session2.session)
    worker_pool.add_proxy_session(f"http://{proxy3.ip}:{proxy3.port}", session3.session)

    # Should get proxy1 (oldest)
    worker = worker_pool.get_worker()
    assert worker.proxy == f"http://{proxy1.ip}:{proxy1.port}"
    worker_pool.release_worker(worker)

    # Update last_used for proxy1
    worker_pool.last_used[f"http://{proxy1.ip}:{proxy1.port}"] = datetime.now(UTC)

    # Should get proxy2 (now oldest)
    worker = worker_pool.get_worker()
    assert worker.proxy == f"http://{proxy2.ip}:{proxy2.port}"

async def test_session_cleanup(worker_pool, mock_story_checker, create_proxy_session):
    """Test session cleanup when removing workers"""
    proxy, session = create_proxy_session()
    worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)

    # Get worker
    worker = worker_pool.get_worker()
    assert worker is not None

    # Remove proxy-session pair
    worker_pool.remove_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)

    # Verify cleanup
    assert f"http://{proxy.ip}:{proxy.port}" not in worker_pool.proxy_sessions
    assert f"http://{proxy.ip}:{proxy.port}" not in worker_pool.last_used
    assert f"http://{proxy.ip}:{proxy.port}" not in worker_pool.proxy_states

async def test_worker_pool_shutdown(worker_pool, mock_story_checker, create_proxy_session):
    """Test worker pool cleanup on shutdown"""
    # Add multiple proxies
    proxies = []
    for i in range(3):
        proxy, session = create_proxy_session(f'http://proxy{i}:8080')
        worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)
        proxies.append(proxy)

    # Get some workers
    workers = []
    for _ in range(2):
        worker = worker_pool.get_worker()
        assert worker is not None
        workers.append(worker)

    # Clean up pool
    for worker in workers:
        worker_pool.release_worker(worker)
        worker_pool.remove_worker(worker)  # Explicitly remove from pools
    for proxy in proxies:
        worker_pool.remove_proxy_session(f"http://{proxy.ip}:{proxy.port}", "session")

    # Verify cleanup
    assert len(worker_pool.proxy_sessions) == 0
    assert len(worker_pool.last_used) == 0
    assert len(worker_pool.proxy_states) == 0
    assert len(worker_pool.active_workers) == 0
    assert len(worker_pool.available_workers) == 0

async def test_worker_initialization_error(worker_pool, create_proxy_session):
    """Test handling of worker initialization errors"""
    proxy, session = create_proxy_session()
    worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)

    # Mock StoryChecker to fail initialization
    with patch('core.worker_manager.StoryChecker', side_effect=Exception("Init failed")):
        # Should handle error gracefully
        worker = worker_pool.get_worker()
        assert worker is None
        assert f"http://{proxy.ip}:{proxy.port}" in worker_pool.proxy_states
