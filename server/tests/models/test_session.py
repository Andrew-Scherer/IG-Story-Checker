"""
Test Session Model
Tests database operations for Instagram session management
"""

import pytest
from datetime import datetime, UTC, timedelta
from sqlalchemy.exc import IntegrityError
from models.session import Session
from models.base import db

@pytest.fixture
def session_data():
    """Test session data"""
    return {
        'cookie': 'test_session_123',
        'status': 'active',
        'proxy_id': None,  # Will be set by test
        'total_checks': 0,
        'successful_checks': 0,
        'last_check': None,
        'cooldown_until': None
    }

def test_session_creation(db_session, session_data):
    """Test creating new session"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    assert session.id is not None
    assert session.cookie == session_data['cookie']
    assert session.status == 'active'
    assert session.total_checks == 0
    assert session.successful_checks == 0
    assert session.success_rate == 1.0  # Default when no checks
    assert session.last_check is None
    assert session.cooldown_until is None
    assert session.created_at is not None
    assert session.updated_at is not None

def test_session_unique_cookie(db_session, session_data):
    """Test session cookie must be unique"""
    # Create first session
    session1 = Session(**session_data)
    db_session.add(session1)
    db_session.commit()
    
    # Try to create second session with same cookie
    session2 = Session(**session_data)
    db_session.add(session2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_session_status_validation(db_session, session_data):
    """Test session status validation"""
    # Test valid statuses
    valid_statuses = ['active', 'cooldown', 'disabled']
    for status in valid_statuses:
        session_data['status'] = status
        session = Session(**session_data)
        db_session.add(session)
        db_session.commit()
        assert session.status == status
    
    # Test invalid status
    session_data['status'] = 'invalid'
    session = Session(**session_data)
    db_session.add(session)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_session_success_rate(db_session, session_data):
    """Test success rate calculation"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    # Initial state
    assert session.success_rate == 1.0
    
    # After some successful checks
    session.total_checks = 10
    session.successful_checks = 8
    db_session.commit()
    
    assert session.success_rate == 0.8
    
    # After failed checks
    session.total_checks = 20
    session.successful_checks = 12
    db_session.commit()
    
    assert session.success_rate == 0.6

def test_session_cooldown(db_session, session_data):
    """Test session cooldown functionality"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    # Set cooldown
    cooldown_until = datetime.now(UTC) + timedelta(minutes=15)
    session.set_cooldown(minutes=15)
    db_session.commit()
    
    assert session.status == 'cooldown'
    assert session.cooldown_until is not None
    assert abs((session.cooldown_until - cooldown_until).total_seconds()) < 1
    
    # Test is_on_cooldown
    assert session.is_on_cooldown() is True
    
    # Test cooldown expiration
    session.cooldown_until = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()
    
    assert session.is_on_cooldown() is False
    
def test_session_check_recording(db_session, session_data):
    """Test recording check results"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    # Record successful check
    session.record_check(success=True)
    db_session.commit()
    
    assert session.total_checks == 1
    assert session.successful_checks == 1
    assert session.last_check is not None
    
    # Record failed check
    session.record_check(success=False)
    db_session.commit()
    
    assert session.total_checks == 2
    assert session.successful_checks == 1

def test_session_proxy_relationship(db_session, session_data):
    """Test session-proxy relationship"""
    from models.proxy import Proxy
    
    # Create proxy
    proxy = Proxy(url='http://test.proxy:8080')
    db_session.add(proxy)
    db_session.commit()
    
    # Create session with proxy
    session_data['proxy_id'] = proxy.id
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    assert session.proxy_id == proxy.id
    assert session.proxy == proxy
    assert session in proxy.sessions

def test_session_soft_delete(db_session, session_data):
    """Test session soft deletion"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    # Soft delete
    session.delete()
    db_session.commit()
    
    # Should not be found in normal query
    assert Session.query.get(session.id) is None
    
    # Should be found with include_deleted
    assert Session.query.with_deleted().get(session.id) is not None
    
    # Status should be disabled
    deleted_session = Session.query.with_deleted().get(session.id)
    assert deleted_session.status == 'disabled'

def test_session_reactivation(db_session, session_data):
    """Test reactivating disabled session"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    # Disable session
    session.status = 'disabled'
    db_session.commit()
    
    # Reactivate
    session.reactivate()
    db_session.commit()
    
    assert session.status == 'active'
    assert session.cooldown_until is None
    assert session.error_count == 0

def test_session_error_tracking(db_session, session_data):
    """Test session error tracking"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    # Record errors
    session.record_error("Test error")
    db_session.commit()
    
    assert session.error_count == 1
    
    # Record more errors
    for _ in range(4):
        session.record_error("Test error")
    db_session.commit()
    
    assert session.error_count == 5
    assert session.status == 'disabled'  # Should be disabled after too many errors
