"""
Test Worker Manager
Tests worker pool management and story checking operations
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch, AsyncMock
from models.batch import Batch, BatchProfile
from models.niche import Niche
from models.profile import Profile
from core.worker_manager import WorkerPool, Worker

@pytest.fixture
def session_cookie():
    """Create test session cookie"""
    return "test_session_123"

@pytest.fixture
def proxy():
    """Create test proxy"""
    return "http://test.proxy:8080"

@pytest.fixture
def worker_pool():
    """Create worker pool for testing"""
    return WorkerPool(max_workers=2)

@pytest.fixture
def niche(db_session):
    """Create test niche"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()
    return niche

@pytest.fixture
def profile(db_session, niche):
    """Create test profile"""
    profile = Profile(username="test_user", niche=niche)
    db_session.add(profile)
    db_session.commit()
    return profile

@pytest.fixture
def batch(db_session, niche):
    """Create test batch"""
    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()
    return batch

@pytest.fixture
def batch_profile(db_session, batch, profile):
    """Create test batch profile"""
    batch_profile = BatchProfile(batch_id=batch.id, profile_id=profile.id)
    db_session.add(batch_profile)
    db_session.commit()
    return batch_profile

@pytest.fixture
def mock_story_checker():
    """Create mock story checker"""
    with patch('core.worker_manager.StoryChecker') as mock:
        checker = Mock()
        mock.return_value = checker
        # Mock async check_profile
        checker.check_profile = AsyncMock(return_value=True)
        # Mock ProxySessionPair attributes
        checker.pair = Mock()
        checker.pair.success_rate = 1.0
        checker.pair.total_checks = 0
        checker.pair.set_cooldown = Mock()
        yield checker

@pytest.mark.asyncio
async def test_worker_creation(worker_pool, mock_story_checker, proxy, session_cookie):
    """Test creating new worker"""
    worker = worker_pool.create_worker(proxy, session_cookie)
    
    assert worker is not None
    assert worker.proxy == proxy
    assert worker.session_cookie == session_cookie
    assert worker.current_profile is None
    assert worker.error_count == 0
    assert worker.last_check is None

def test_proxy_session_management(worker_pool, proxy, session_cookie):
    """Test managing proxy-session pairs"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    assert proxy in worker_pool.proxy_sessions
    assert len(worker_pool.proxy_sessions[proxy]) == 1
    assert worker_pool.proxy_sessions[proxy][0] == (session_cookie, 1.0)
    
    # Remove proxy-session pair
    worker_pool.remove_proxy_session(proxy, session_cookie)
    assert proxy not in worker_pool.proxy_sessions

def test_worker_allocation(worker_pool, mock_story_checker, proxy, session_cookie):
    """Test getting worker from pool"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    
    # Get first worker
    worker1 = worker_pool.get_worker()
    assert worker1 is not None
    assert len(worker_pool.active_workers) == 1
    
    # Add another proxy-session pair
    worker_pool.add_proxy_session("proxy2", "session2")
    
    # Get second worker
    worker2 = worker_pool.get_worker()
    assert worker2 is not None
    assert worker1 != worker2
    assert len(worker_pool.active_workers) == 2
    
    # Should not get more workers than max
    worker3 = worker_pool.get_worker()
    assert worker3 is None
    assert len(worker_pool.active_workers) == 2

def test_worker_release(worker_pool, mock_story_checker, proxy, session_cookie):
    """Test releasing worker back to pool"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    
    # Get and release worker
    worker = worker_pool.get_worker()
    assert len(worker_pool.active_workers) == 1
    
    worker_pool.release_worker(worker)
    assert len(worker_pool.active_workers) == 0
    assert len(worker_pool.available_workers) == 1

@pytest.mark.asyncio
async def test_story_checking(worker_pool, mock_story_checker, batch_profile, db_session, proxy, session_cookie):
    """Test checking story for profile"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    worker = worker_pool.get_worker()
    
    # Check story
    result = await worker.check_story(batch_profile)
    assert result is True
    
    # Verify profile was checked
    mock_story_checker.check_profile.assert_called_once_with(batch_profile.profile.username)
    
    # Verify batch profile updated
    db_session.refresh(batch_profile)
    assert batch_profile.status == 'completed'
    assert batch_profile.has_story is True

@pytest.mark.asyncio
async def test_story_check_error(worker_pool, mock_story_checker, batch_profile, proxy, session_cookie):
    """Test handling story check error"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    worker = worker_pool.get_worker()
    
    # Simulate error
    mock_story_checker.check_profile.side_effect = Exception("Test error")
    
    # Check should handle error
    result = await worker.check_story(batch_profile)
    assert result is False
    assert worker.error_count == 1

@pytest.mark.asyncio
async def test_worker_error_threshold(worker_pool, mock_story_checker, batch_profile, proxy, session_cookie):
    """Test worker disabled after too many errors"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    worker = worker_pool.get_worker()
    
    # Simulate multiple errors
    mock_story_checker.check_profile.side_effect = Exception("Test error")
    
    for _ in range(worker.MAX_ERRORS):
        await worker.check_story(batch_profile)
    
    # Worker should be disabled
    assert worker.is_disabled
    assert worker not in worker_pool.available_workers
    assert worker not in worker_pool.active_workers

def test_session_update(worker_pool, mock_story_checker, proxy, session_cookie):
    """Test updating proxy-session pair"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    worker = worker_pool.get_worker()
    
    # Update session
    new_proxy = "http://new.proxy:8080"
    new_session = "new_session_456"
    worker.update_session(new_proxy, new_session)
    
    assert worker.proxy == new_proxy
    assert worker.session_cookie == new_session
    assert worker.error_count == 0
    assert not worker.is_disabled
    assert not worker.is_rate_limited

@pytest.mark.asyncio
async def test_concurrent_story_checks(worker_pool, mock_story_checker, db_session, batch, proxy, session_cookie):
    """Test checking multiple profiles concurrently"""
    # Add proxy-session pairs
    worker_pool.add_proxy_session(proxy, session_cookie)
    worker_pool.add_proxy_session("proxy2", "session2")
    
    # Create multiple profiles
    profiles = []
    for i in range(3):
        profile = Profile(username=f"test_user_{i}", niche=batch.niche)
        db_session.add(profile)
        db_session.commit()
        
        batch_profile = BatchProfile(batch_id=batch.id, profile_id=profile.id)
        db_session.add(batch_profile)
        db_session.commit()
        profiles.append(batch_profile)
    
    # Check stories concurrently
    results = []
    for profile in profiles:
        worker = worker_pool.get_worker()
        if worker:
            result = await worker.check_story(profile)
            results.append(result)
            worker_pool.release_worker(worker)
    
    # Verify results
    assert len(results) == 3
    assert all(results)  # All checks should succeed
    assert mock_story_checker.check_profile.call_count == 3

@pytest.mark.asyncio
async def test_rate_limiting(worker_pool, mock_story_checker, batch_profile, proxy, session_cookie):
    """Test rate limit handling"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    worker = worker_pool.get_worker()
    
    # Simulate rate limit
    mock_story_checker.check_profile.side_effect = [
        Exception("Rate limited"),  # First call fails
        True  # Second call succeeds after waiting
    ]
    
    # First check should fail
    result = await worker.check_story(batch_profile)
    assert result is False
    
    # Should be in cooldown
    assert worker.is_rate_limited
    assert worker not in worker_pool.available_workers
    
    # Verify cooldown was set
    mock_story_checker.pair.set_cooldown.assert_called_once()
    
    # After cooldown, should work
    worker.clear_rate_limit()
    mock_story_checker.check_profile.side_effect = None  # Reset side effect
    mock_story_checker.check_profile.return_value = True  # Set success
    result = await worker.check_story(batch_profile)
    assert result is True

@pytest.mark.asyncio
async def test_success_rate_tracking(worker_pool, mock_story_checker, batch_profile, proxy, session_cookie):
    """Test tracking success rates for proxy-session pairs"""
    # Add proxy-session pair
    worker_pool.add_proxy_session(proxy, session_cookie)
    worker = worker_pool.get_worker()
    
    # Simulate successful check
    mock_story_checker.pair.success_rate = 1.0
    mock_story_checker.pair.total_checks = 1
    await worker.check_story(batch_profile)
    worker_pool.release_worker(worker)
    
    # Verify success rate updated
    assert worker_pool.proxy_sessions[proxy][0][1] == 1.0
    
    # Simulate failed check
    worker = worker_pool.get_worker()
    mock_story_checker.check_profile.side_effect = Exception("Test error")
    mock_story_checker.pair.success_rate = 0.5
    mock_story_checker.pair.total_checks = 2
    await worker.check_story(batch_profile)
    worker_pool.release_worker(worker)
    
    # Verify success rate updated
    assert worker_pool.proxy_sessions[proxy][0][1] == 0.5
