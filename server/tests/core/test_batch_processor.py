"""
Test batch processor core functionality with Celery
Tests the complete flow of batch processing including:
- Celery task execution
- Batch state transitions
- Profile processing
- Error handling
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch
from celery.contrib.testing.worker import start_worker
from server.models import Batch, Niche, Profile, Proxy, Session
from server.models.proxy import ProxyStatus
from server.core.batch_processor import process_batch, enqueue_batches
from server.core.proxy_session_manager import ProxySessionManager
from server.app import celery

@pytest.fixture(scope='module')
def celery_config():
    """Configure Celery for testing"""
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,  # Tasks run synchronously in tests
    }

@pytest.fixture(scope='module')
def celery_enable_logging():
    """Enable Celery logging in tests"""
    return True

@pytest.fixture(scope='module')
def celery_includes():
    """Include task modules"""
    return ['server.core.batch_processor']

@pytest.fixture
def mock_proxy_session_manager():
    """Create a mock proxy session manager for testing"""
    manager = Mock(spec=ProxySessionManager)
    manager.get_next_proxy = Mock()
    manager.is_proxy_healthy = Mock(return_value=True)
    return manager

def test_should_complete_batch_successfully(app, db_session, mock_proxy_session_manager, test_batch):
    """Test that batch is completed successfully when all profiles are processed"""
    # Arrange
    proxy = Proxy(
        ip="127.0.0.1",
        port=8080,
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

    mock_proxy_session_manager.get_next_proxy.return_value = proxy

    # Act
    with patch('server.core.batch_processor.ProxySessionManager', return_value=mock_proxy_session_manager), \
         patch('server.core.story_checker.StoryChecker.check_story', return_value=True):
        process_batch.delay(test_batch.id)

    # Assert
    batch = db_session.get(Batch, test_batch.id)
    assert batch.status == 'done'
    assert batch.position is None
    assert batch.completed_at is not None
    assert batch.successful_checks == 1
    assert batch.failed_checks == 0

def test_should_handle_story_check_error(app, db_session, mock_proxy_session_manager, test_batch):
    """Test that batch handles story check errors appropriately"""
    # Arrange
    proxy = Proxy(
        ip="127.0.0.1",
        port=8080,
        is_active=True,
        status=ProxyStatus.ACTIVE
    )
    db_session.add(proxy)
    db_session.commit()

    mock_proxy_session_manager.get_next_proxy.return_value = proxy

    # Act
    with patch('server.core.batch_processor.ProxySessionManager', return_value=mock_proxy_session_manager), \
         patch('server.core.story_checker.StoryChecker.check_story', side_effect=Exception("Test error")):
        process_batch.delay(test_batch.id)

    # Assert
    batch = db_session.get(Batch, test_batch.id)
    assert batch.status == 'error'
    assert batch.position is None
    assert batch.error is not None
    assert batch.successful_checks == 0
    assert batch.failed_checks == 1

def test_should_pause_batch_when_no_proxies(app, db_session, mock_proxy_session_manager, test_batch):
    """Test that batch is paused when no proxies are available"""
    # Arrange
    mock_proxy_session_manager.get_next_proxy.return_value = None

    # Act
    with patch('server.core.batch_processor.ProxySessionManager', return_value=mock_proxy_session_manager):
        process_batch.delay(test_batch.id)

    # Assert
    batch = db_session.get(Batch, test_batch.id)
    assert batch.status == 'paused'
    assert batch.position is None
    assert batch.error is not None

def test_should_promote_next_batch_when_queue_available(app, db_session, mock_proxy_session_manager, test_batch):
    """Test that next batch in queue is promoted when available"""
    # Arrange
    test_batch.status = 'queued'
    test_batch.position = 1
    db_session.commit()

    proxy = Proxy(
        ip="127.0.0.1",
        port=8080,
        is_active=True,
        status=ProxyStatus.ACTIVE
    )
    db_session.add(proxy)
    db_session.commit()

    mock_proxy_session_manager.get_next_proxy.return_value = proxy

    # Act
    with patch('server.core.batch_processor.ProxySessionManager', return_value=mock_proxy_session_manager), \
         patch('server.core.story_checker.StoryChecker.check_story', return_value=True):
        enqueue_batches()

    # Assert
    db_session.refresh(test_batch)
    assert test_batch.status == 'done'
    assert test_batch.position is None
    assert test_batch.completed_at is not None

@pytest.mark.real_db
def test_should_process_batch_with_real_proxy(app, db_session, test_batch):
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
    with patch('server.core.story_checker.StoryChecker.check_story', return_value=True):
        process_batch.delay(test_batch.id)

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
