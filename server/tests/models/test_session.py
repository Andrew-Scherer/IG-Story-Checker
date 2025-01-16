"""
Test Session Model
Tests database operations for Instagram session management
"""

import pytest
from sqlalchemy.exc import IntegrityError
from models.session import Session
from models.proxy import Proxy

@pytest.fixture
def session_data():
    """Test session data"""
    return {
        'session': 'test_session_123',
        'status': 'active',
        'proxy_id': None  # Will be set by test
    }

def test_session_creation(db_session, session_data):
    """Test creating new session"""
    session = Session(**session_data)
    db_session.add(session)
    db_session.commit()
    
    assert session.id is not None
    assert session.session == session_data['session']
    assert session.status == 'active'
    assert session.created_at is not None
    assert session.updated_at is not None

def test_session_unique_session(db_session, session_data):
    """Test session must be unique"""
    # Create first session
    session1 = Session(**session_data)
    db_session.add(session1)
    db_session.commit()
    
    # Try to create second session with same session data
    session2 = Session(**session_data)
    db_session.add(session2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_session_status_validation(db_session, session_data):
    """Test session status validation"""
    # Test valid statuses
    valid_statuses = ['active', 'disabled']
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

def test_session_proxy_relationship(db_session, session_data):
    """Test session-proxy relationship"""
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
