"""
Test session model functionality
"""
import pytest
from models.session import Session
from models.proxy import Proxy

def test_session_creation(db_session):
    """Test creating session with basic info"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True
    )
    db_session.add(proxy)

    session = Session(
        proxy=proxy,
        session='test_session_cookie',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session)
    db_session.commit()

    assert session.id is not None
    assert session.session == 'test_session_cookie'
    assert session.status == Session.STATUS_ACTIVE
    assert session.proxy_id == proxy.id
    assert session.created_at is not None
    assert session.updated_at is not None

def test_session_unique_constraint(db_session):
    """Test unique constraint on session cookie"""
    proxy1 = Proxy(ip='192.168.1.1', port=8080)
    proxy2 = Proxy(ip='192.168.1.2', port=8080)
    db_session.add_all([proxy1, proxy2])
    db_session.commit()

    # Create first session
    session1 = Session(
        proxy=proxy1,
        session='test_session',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session1)
    db_session.commit()

    # Try to create duplicate session
    session2 = Session(
        proxy=proxy2,
        session='test_session',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session2)
    with pytest.raises(Exception) as exc:
        db_session.commit()
    assert 'sessions_session_key' in str(exc.value)

def test_session_proxy_relationship(db_session):
    """Test session-proxy relationship"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True
    )
    db_session.add(proxy)

    session = Session(
        proxy=proxy,
        session='test_session',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session)
    db_session.commit()

    # Test relationship from both sides
    assert session.proxy == proxy
    assert len(proxy.sessions.all()) == 1
    assert proxy.sessions[0] == session

def test_session_status_validation(db_session):
    """Test session status validation"""
    proxy = Proxy(ip='192.168.1.1', port=8080)
    db_session.add(proxy)
    db_session.commit()

    # Valid status
    session = Session(
        proxy=proxy,
        session='test_session',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session)
    db_session.commit()

    # Invalid status
    session.status = 'invalid'
    with pytest.raises(Exception) as exc:
        db_session.commit()
    assert 'session_status' in str(exc.value)

def test_session_serialization(db_session):
    """Test session serialization to dict"""
    proxy = Proxy(ip='192.168.1.1', port=8080)
    db_session.add(proxy)
    db_session.commit()

    session = Session(
        proxy=proxy,
        session='test_session',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session)
    db_session.commit()

    data = session.to_dict()
    assert data['id'] == session.id
    assert data['session'] == session.session
    assert data['status'] == session.status
    assert data['proxy_id'] == session.proxy_id
    assert data['created_at'] == session.created_at.isoformat()
    assert data['updated_at'] == session.updated_at.isoformat()

def test_session_status_transitions(db_session):
    """Test session status transitions"""
    proxy = Proxy(ip='192.168.1.1', port=8080)
    db_session.add(proxy)

    session = Session(
        proxy=proxy,
        session='test_session',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session)
    db_session.commit()

    # Test valid transition
    session.status = Session.STATUS_DISABLED
    db_session.commit()
    assert session.status == Session.STATUS_DISABLED

def test_session_proxy_unique_constraint(db_session):
    """Test one session per proxy constraint"""
    proxy = Proxy(ip='192.168.1.1', port=8080)
    db_session.add(proxy)
    db_session.commit()

    # Create first session
    session1 = Session(
        proxy=proxy,
        session='test_session1',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session1)
    db_session.commit()

    # Try to create second session for same proxy
    session2 = Session(
        proxy=proxy,
        session='test_session2',
        status=Session.STATUS_ACTIVE
    )
    db_session.add(session2)
    with pytest.raises(Exception) as exc:
        db_session.commit()
    assert 'proxy_id' in str(exc.value)

def test_session_string_representation(db_session):
    """Test string representation of session"""
    proxy = Proxy(ip='192.168.1.1', port=8080)
    db_session.add(proxy)

    session = Session(
        proxy=proxy,
        session='test_session',
        status=Session.STATUS_ACTIVE
    )
    assert repr(session) == '<Session None (active)>'

    db_session.add(session)
    db_session.commit()

    assert repr(session) == f'<Session {session.id} (active)>'
