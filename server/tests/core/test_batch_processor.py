"""
Test batch processor core functionality
"""

"""
Test batch processor core functionality
Tests the complete flow of batch processing including:
- Worker pool management
- Batch state transitions
- Profile processing
- Error handling
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch
from server.models import Batch, Niche, Profile, Proxy, Session
from server.models.proxy import ProxyStatus
from server.core.batch_processor import BatchProcessor, process_batches
from server.core.worker.pool import WorkerPool

@pytest.fixture
def mock_worker():
    """Create a mock worker for testing"""
    worker = Mock()
    worker.check_story = AsyncMock()
    worker.is_disabled = False
    worker.is_rate_limited = False
    return worker

@pytest.fixture
def mock_worker_pool():
    """Create a mock worker pool for testing"""
    pool = Mock(spec=WorkerPool)
    pool.get_worker = Mock()
    pool.release_worker = AsyncMock()
    pool.add_proxies = Mock()
    return pool

@pytest.mark.asyncio
async def test_should_complete_batch_successfully(app, db_session, mock_worker, mock_worker_pool, test_batch):
    """Test that batch is completed successfully when all profiles are processed"""
    # Arrange
    mock_worker.check_story.return_value = (True, True)  # success, has_story
    mock_worker_pool.get_worker.return_value = mock_worker
    
    # Act
    processor = BatchProcessor(db_session, mock_worker_pool)
    await processor._process_batch_async(test_batch.id, mock_worker_pool)
    
    # Assert
    batch = db_session.get(Batch, test_batch.id)
    assert batch.status == 'done'
    assert batch.position is None
    assert batch.completed_at is not None
    assert batch.successful_checks == 1
    assert batch.failed_checks == 0
    mock_worker_pool.get_worker.assert_called_once()
    mock_worker_pool.release_worker.assert_called_once_with(mock_worker)

@pytest.mark.asyncio
async def test_should_handle_story_check_error(app, db_session, mock_worker, mock_worker_pool, test_batch):
    """Test that batch handles story check errors appropriately"""
    # Arrange
    mock_worker.check_story.side_effect = Exception("Test error")
    mock_worker_pool.get_worker.return_value = mock_worker
    
    # Act
    processor = BatchProcessor(db_session, mock_worker_pool)
    await processor._process_batch_async(test_batch.id, mock_worker_pool)
    
    # Assert
    batch = db_session.get(Batch, test_batch.id)
    assert batch.status == 'error'
    assert batch.position is None
    assert batch.error is not None
    assert batch.successful_checks == 0
    assert batch.failed_checks == 1

@pytest.mark.asyncio
async def test_should_pause_batch_when_no_workers(app, db_session, mock_worker_pool, test_batch):
    """Test that batch is paused when no workers are available"""
    # Arrange
    mock_worker_pool.get_worker.return_value = None
    
    # Act
    processor = BatchProcessor(db_session, mock_worker_pool)
    await processor._process_batch_async(test_batch.id, mock_worker_pool)
    
    # Assert
    batch = db_session.get(Batch, test_batch.id)
    assert batch.status == 'paused'
    assert batch.position is None
    assert batch.error is not None

@pytest.mark.asyncio
async def test_should_promote_next_batch_when_queue_available(app, db_session, mock_worker_pool, test_batch):
    """Test that next batch in queue is promoted when available"""
    # Arrange
    test_batch.status = 'queued'
    test_batch.position = 1
    db_session.commit()
    
    mock_worker = Mock()
    mock_worker.check_story = AsyncMock(return_value=(True, True))
    mock_worker.is_disabled = False
    mock_worker.is_rate_limited = False
    mock_worker_pool.get_worker.return_value = mock_worker
    
    # Act
    with app.app_context():
        await process_batches(db_session, mock_worker_pool)
    
    # Assert
    db_session.refresh(test_batch)
    assert test_batch.status == 'done'
    assert test_batch.position is None
    assert test_batch.completed_at is not None

@pytest.mark.real_db
@pytest.mark.asyncio
async def test_should_process_batch_with_real_proxy(app, db_session, test_batch):
    """Test batch processing with real proxy and session"""
    # Arrange
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
    
    session = Session(
        proxy_id=proxy.id,
        session="test_session",
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session)
    db_session.commit()
    
    # Act
    with patch('server.core.story_checker.StoryChecker.check_story') as mock_check_story:
        mock_check_story.return_value = True
        worker_pool = WorkerPool(5)
        worker_pool.add_proxies([proxy])
        processor = BatchProcessor(db_session, worker_pool)
        await processor._process_batch_async(test_batch.id, worker_pool)
    
    # Assert
    batch = db_session.get(Batch, test_batch.id)
    assert batch.status == 'done'
    assert batch.position is None
    assert batch.completed_at is not None
    assert batch.successful_checks == 1
    assert batch.failed_checks == 0
    
    proxy = db_session.get(Proxy, proxy.id)
    assert proxy.total_requests == 1
    assert proxy.failed_requests == 0
    assert proxy.last_used is not None
