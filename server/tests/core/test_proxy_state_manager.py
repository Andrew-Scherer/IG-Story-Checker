"""Tests for ProxyStateManager"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
from core.proxy_state_manager import ProxyStateManager, ProxySessionState
from models.proxy import Proxy, ProxyStatus
from models.session import Session
from models.proxy_error_log import ProxyErrorLog

@pytest.fixture
def app():
    """Create test Flask app"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def mock_proxy():
    """Create mock proxy without using SQLAlchemy model"""
    proxy = Mock()
    proxy.id = "test-proxy-1"
    proxy.status = ProxyStatus.ACTIVE
    proxy.configure_mock(**{
        'id': 'test-proxy-1',
        'status': ProxyStatus.ACTIVE
    })
    return proxy

@pytest.fixture
def mock_session():
    """Create mock session without using SQLAlchemy model"""
    session = Mock()
    session.configure_mock(**{
        'id': 'test-session-1',
        'status': Session.STATUS_ACTIVE
    })
    return session

@pytest.fixture
def mock_error_log():
    """Create mock error log"""
    error_log = Mock()
    error_log.configure_mock(**{
        'error_message': 'Test error',
        'state_change': False,
        'timestamp': datetime.now(UTC)
    })
    return error_log

@pytest.fixture
def db_session():
    """Create mock database session"""
    session = Mock()
    session.commit = Mock()
    session.add = Mock()
    
    # Configure query mock
    query_mock = Mock()
    query_mock.filter_by = Mock(return_value=query_mock)
    query_mock.order_by = Mock(return_value=query_mock)
    query_mock.limit = Mock(return_value=query_mock)
    query_mock.all = Mock(return_value=[])
    query_mock.first = Mock(return_value=None)
    
    session.query = Mock(return_value=query_mock)
    return session

@pytest.fixture
def proxy_log_service():
    """Create mock proxy log service"""
    service = Mock()
    service.log_state_change = Mock()
    return service

@pytest.fixture
def state_manager(db_session, proxy_log_service):
    """Create ProxyStateManager instance"""
    return ProxyStateManager(db_session, proxy_log_service)

class TestStateRetrieval:
    """Tests for state retrieval"""

    def test_get_proxy_state_active(self, app, state_manager, mock_proxy, db_session):
        """Test getting state of active proxy"""
        with app.app_context():
            db_session.query().filter_by().first.return_value = mock_proxy
            state = state_manager.get_state(mock_proxy.id)
            assert state == ProxySessionState.ACTIVE

    def test_get_proxy_state_disabled(self, app, state_manager, mock_proxy, db_session):
        """Test getting state of disabled proxy"""
        with app.app_context():
            mock_proxy.status = ProxyStatus.DISABLED
            db_session.query().filter_by().first.return_value = mock_proxy
            state = state_manager.get_state(mock_proxy.id)
            assert state == ProxySessionState.DISABLED

    def test_get_session_state_active(self, app, state_manager, mock_session, db_session):
        """Test getting state of active session"""
        with app.app_context():
            db_session.query().filter_by().first.return_value = mock_session
            state = state_manager.get_session_state(mock_session.id)
            assert state == ProxySessionState.ACTIVE

    def test_get_session_state_disabled(self, app, state_manager, mock_session, db_session):
        """Test getting state of disabled session"""
        with app.app_context():
            mock_session.status = Session.STATUS_DISABLED
            db_session.query().filter_by().first.return_value = mock_session
            state = state_manager.get_session_state(mock_session.id)
            assert state == ProxySessionState.DISABLED

class TestStateTransitions:
    """Tests for state transitions"""

    def test_disable_proxy(self, app, state_manager, mock_proxy, db_session):
        """Test disabling a proxy"""
        with app.app_context():
            db_session.query().filter_by().first.return_value = mock_proxy
            success = state_manager.transition_proxy_state(
                mock_proxy.id,
                ProxySessionState.DISABLED,
                "Test disable"
            )
            assert success is True
            assert mock_proxy.status == ProxyStatus.DISABLED
            db_session.add.assert_called_once()
            db_session.commit.assert_called_once()

    def test_disable_session(self, app, state_manager, mock_session, db_session):
        """Test disabling a session"""
        with app.app_context():
            db_session.query().filter_by().first.return_value = mock_session
            success = state_manager.transition_session_state(
                mock_session.id,
                ProxySessionState.DISABLED,
                "Test disable"
            )
            assert success is True
            assert mock_session.status == Session.STATUS_DISABLED
            db_session.add.assert_called_once()
            db_session.commit.assert_called_once()

class TestRetryLogic:
    """Tests for retry logic"""

    def test_handle_failure(self, app, state_manager, mock_proxy, mock_session, db_session, mock_error_log):
        """Test handling a failed request"""
        with app.app_context():
            db_session.query().filter_by().first.side_effect = [mock_proxy, mock_session]
            db_session.query().filter_by().order_by().limit().all.return_value = []

            state_manager.handle_request_result(
                mock_proxy.id,
                mock_session.id,
                success=False,
                error="Test error"
            )

            db_session.add.assert_called_once()
            db_session.commit.assert_called_once()

    def test_max_retries_exceeded(self, app, state_manager, mock_proxy, mock_session, db_session, mock_error_log):
        """Test handling max retries exceeded"""
        with app.app_context():
            # Setup mocks to simulate max retries
            error_logs = [mock_error_log] * (state_manager.max_retries - 1)
            db_session.query().filter_by().order_by().limit().all.return_value = error_logs
            db_session.query().filter_by().first.side_effect = [mock_proxy, mock_session]

            state_manager.handle_request_result(
                mock_proxy.id,
                mock_session.id,
                success=False,
                error="Test error"
            )

            # Verify proxy and session were disabled
            assert mock_proxy.status == ProxyStatus.DISABLED
            assert mock_session.status == Session.STATUS_DISABLED

class TestActiveEntities:
    """Tests for retrieving active entities"""

    def test_get_active_proxies(self, app, state_manager, mock_proxy, db_session):
        """Test getting active proxies"""
        with app.app_context():
            db_session.query().filter_by().all.return_value = [mock_proxy]
            active_proxies = state_manager.get_active_proxies()
            assert len(active_proxies) == 1
            assert active_proxies[0] == mock_proxy

    def test_get_active_sessions(self, app, state_manager, mock_session, db_session):
        """Test getting active sessions"""
        with app.app_context():
            db_session.query().filter_by().all.return_value = [mock_session]
            active_sessions = state_manager.get_active_sessions()
            assert len(active_sessions) == 1
            assert active_sessions[0] == mock_session