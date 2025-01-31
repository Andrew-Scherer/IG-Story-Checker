"""
End-to-end tests for batch processing workflow
Tests the complete flow of batch processing including:
- Worker pool initialization
- Proxy and session management
- Batch processing
- Story checking
- Error handling
"""

import pytest
import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch
from server.models import db, Profile, Batch, Niche, Proxy, Session
from server.models.proxy import ProxyStatus
from server.core.batch_processor import BatchProcessor
from server.core.worker.pool import WorkerPool
from server.services.batch_manager import BatchManager

@pytest.fixture
def test_proxy(db_session):
    """Create a test proxy"""
    proxy = Proxy(
        ip="127.0.0.1",
        port=8080,
        username="testuser",
        password="testpass",
        is_active=True,
        status=ProxyStatus.ACTIVE
    )
    db_session.add(proxy)
    db_session.commit()
    return proxy

@pytest.fixture
def test_session(db_session, test_proxy):
    """Create a test session"""
    session = Session(
        proxy_id=test_proxy.id,
        session="test_session",
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session)
    db_session.commit()
    return session

@pytest.fixture
def test_batch_with_profiles(db_session):
    """Create a test batch with profiles"""
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.commit()

    profiles = [
        Profile(username=f'test{i}', niche_id=niche.id, status='active')
        for i in range(3)
    ]
    db_session.add_all(profiles)
    db_session.commit()

    batch = Batch(niche_id=niche.id, profile_ids=[p.id for p in profiles])
    batch.status = 'queued'
    batch.position = 1
    db_session.add(batch)
    db_session.commit()
    return batch

@pytest.mark.asyncio
async def test_worker_pool_initialization(db_session, test_proxy, test_session):
    """Test worker pool initialization and proxy assignment"""
    # Initialize worker pool
    worker_pool = WorkerPool(5)
    
    # Add proxy to pool
    worker_pool.add_proxies([test_proxy])
    
    # Get worker and verify it's properly configured
    worker = worker_pool.get_worker()
    assert worker is not None
    assert worker.proxy_session.proxy.id == test_proxy.id
    assert worker.proxy_session.session.id == test_session.id
    assert not worker.is_disabled
    assert not worker.is_rate_limited

@pytest.mark.asyncio
async def test_batch_processing_success(db_session, test_proxy, test_session, test_batch_with_profiles):
    """Test successful batch processing flow"""
    # Mock story checker to avoid real HTTP requests
    with patch('core.story_checker.StoryChecker.check_story', new_callable=AsyncMock) as mock_check_story:
        mock_check_story.return_value = True  # Simulate story found
        
        # Initialize worker pool with proxy
        worker_pool = WorkerPool(5)
        worker_pool.add_proxies([test_proxy])
        
        # Process batch
        processor = BatchProcessor(db_session, worker_pool)
        await processor._process_batch_async(test_batch_with_profiles.id, worker_pool)
        
        # Verify batch completed successfully
        db_session.refresh(test_batch_with_profiles)
        assert test_batch_with_profiles.status == 'done'
        assert test_batch_with_profiles.position is None
        assert test_batch_with_profiles.completed_at is not None
        assert test_batch_with_profiles.successful_checks == 3
        assert test_batch_with_profiles.failed_checks == 0
        
        # Verify profiles were updated
        for profile in test_batch_with_profiles.profiles:
            db_session.refresh(profile)
            assert profile.total_checks == 1
            assert profile.active_story is True
            assert profile.last_story_detected is not None

@pytest.mark.asyncio
async def test_batch_processing_with_retries(db_session, test_proxy, test_session, test_batch_with_profiles):
    """Test batch processing with retries on failure"""
    # Mock story checker to fail first time, succeed second time
    check_story_calls = 0
    async def mock_check_story(*args, **kwargs):
        nonlocal check_story_calls
        check_story_calls += 1
        if check_story_calls == 1:
            raise Exception("Network error")
        return True

    with patch('core.story_checker.StoryChecker.check_story', new=mock_check_story):
        # Initialize worker pool with proxy
        worker_pool = WorkerPool(5)
        worker_pool.add_proxies([test_proxy])
        
        # Process batch
        processor = BatchProcessor(db_session, worker_pool)
        await processor._process_batch_async(test_batch_with_profiles.id, worker_pool)
        
        # Verify batch was retried and completed
        db_session.refresh(test_batch_with_profiles)
        assert test_batch_with_profiles.status == 'done'
        assert test_batch_with_profiles.successful_checks > 0
        assert test_batch_with_profiles.failed_checks > 0

@pytest.mark.asyncio
async def test_batch_processing_no_workers(db_session, test_batch_with_profiles):
    """Test batch processing when no workers are available"""
    # Initialize empty worker pool
    worker_pool = WorkerPool(5)
    
    # Process batch
    processor = BatchProcessor(db_session, worker_pool)
    await processor._process_batch_async(test_batch_with_profiles.id, worker_pool)
    
    # Verify batch was paused
    db_session.refresh(test_batch_with_profiles)
    assert test_batch_with_profiles.status == 'paused'
    assert test_batch_with_profiles.position is None
    assert test_batch_with_profiles.error is not None

@pytest.mark.asyncio
async def test_batch_processing_rate_limit(db_session, test_proxy, test_session, test_batch_with_profiles):
    """Test batch processing with rate limiting"""
    # Mock story checker to simulate rate limit
    async def mock_check_story(*args, **kwargs):
        raise Exception("Rate limited")

    with patch('core.story_checker.StoryChecker.check_story', new=mock_check_story):
        # Initialize worker pool with proxy
        worker_pool = WorkerPool(5)
        worker_pool.add_proxies([test_proxy])
        
        # Process batch
        processor = BatchProcessor(db_session, worker_pool)
        await processor._process_batch_async(test_batch_with_profiles.id, worker_pool)
        
        # Verify batch handling of rate limit
        db_session.refresh(test_batch_with_profiles)
        assert test_batch_with_profiles.status in ('paused', 'error')  # Either is acceptable
        assert test_batch_with_profiles.error is not None
        assert "Rate limited" in test_batch_with_profiles.error

@pytest.mark.asyncio
async def test_batch_state_transitions(db_session, test_proxy, test_session, test_batch_with_profiles):
    """Test batch state transitions during processing"""
    # Mock story checker with delay to observe transitions
    async def mock_check_story(*args, **kwargs):
        await asyncio.sleep(0.1)  # Small delay
        return True

    with patch('core.story_checker.StoryChecker.check_story', new=mock_check_story):
        # Initialize worker pool with proxy
        worker_pool = WorkerPool(5)
        worker_pool.add_proxies([test_proxy])
        
        # Start processing batch
        processor = BatchProcessor(db_session, worker_pool)
        process_task = asyncio.create_task(
            processor._process_batch_async(test_batch_with_profiles.id, worker_pool)
        )
        
        # Allow some processing time
        await asyncio.sleep(0.2)
        
        # Verify intermediate state
        db_session.refresh(test_batch_with_profiles)
        assert test_batch_with_profiles.status == 'running'
        assert test_batch_with_profiles.position == 0
        
        # Complete processing
        await process_task
        
        # Verify final state
        db_session.refresh(test_batch_with_profiles)
        assert test_batch_with_profiles.status == 'done'
        assert test_batch_with_profiles.position is None
        assert test_batch_with_profiles.completed_at is not None