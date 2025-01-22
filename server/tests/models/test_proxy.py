"""
Test proxy model functionality
"""
import pytest
from datetime import datetime, UTC, timedelta
from models.proxy import Proxy, ProxyStatus
from models.session import Session

def test_proxy_creation(db_session):
    """Test creating proxy with basic info"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        username='test_user',
        password='test_pass',
        is_active=True
    )
    db_session.add(proxy)
    db_session.commit()

    assert proxy.id is not None
    assert proxy.ip == '192.168.1.1'
    assert proxy.port == 8080
    assert proxy.username == 'test_user'
    assert proxy.password == 'test_pass'
    assert proxy.is_active is True
    assert proxy.total_requests == 0
    assert proxy.failed_requests == 0
    assert proxy.requests_this_hour == 0
    assert proxy.error_count == 0
    assert proxy.created_at is not None
    assert proxy.updated_at is not None

def test_proxy_session_relationship(db_session):
    """Test proxy-session relationship"""
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

    assert len(proxy.sessions.all()) == 1
    assert proxy.sessions[0].session == 'test_session'
    assert proxy.sessions[0].status == Session.STATUS_ACTIVE

def test_proxy_unique_constraint(db_session):
    """Test unique constraint on ip+port"""
    proxy1 = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True
    )
    db_session.add(proxy1)
    db_session.commit()

    # Try to create duplicate
    proxy2 = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True
    )
    db_session.add(proxy2)
    with pytest.raises(Exception) as exc:
        db_session.commit()
    assert 'uix_proxy_ip_port' in str(exc.value)

def test_proxy_status_property(db_session):
    """Test proxy status property"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True
    )
    assert proxy.status == ProxyStatus.ACTIVE

    proxy.is_active = False
    assert proxy.status == ProxyStatus.DISABLED

def test_record_request(db_session):
    """Test recording request results"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True
    )
    db_session.add(proxy)
    db_session.commit()

    # Successful request
    proxy.record_request(success=True)
    assert proxy.total_requests == 1
    assert proxy.failed_requests == 0
    assert proxy.requests_this_hour == 1
    assert proxy.error_count == 0

    # Failed request
    proxy.record_request(success=False)
    assert proxy.total_requests == 2
    assert proxy.failed_requests == 1
    assert proxy.requests_this_hour == 2
    assert proxy.error_count == 1

    # Successful request resets error count
    proxy.record_request(success=True)
    assert proxy.total_requests == 3
    assert proxy.failed_requests == 1
    assert proxy.requests_this_hour == 3
    assert proxy.error_count == 0

def test_reset_hourly_count(db_session):
    """Test resetting hourly request counter"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True,
        requests_this_hour=50
    )
    db_session.add(proxy)
    db_session.commit()

    proxy.reset_hourly_count()
    assert proxy.requests_this_hour == 0
    assert proxy.updated_at > proxy.created_at

def test_proxy_serialization(db_session):
    """Test proxy serialization to dict"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        username='test_user',
        password='test_pass',
        is_active=True,
        total_requests=100,
        failed_requests=10,
        requests_this_hour=5,
        error_count=0
    )
    db_session.add(proxy)
    db_session.commit()

    data = proxy.to_dict()
    assert data['ip'] == proxy.ip
    assert data['port'] == proxy.port
    assert data['username'] == proxy.username
    assert data['password'] == proxy.password
    assert data['is_active'] == proxy.is_active
    assert data['status'] == proxy.status.value
    assert data['total_requests'] == proxy.total_requests
    assert data['failed_requests'] == proxy.failed_requests
    assert data['requests_this_hour'] == proxy.requests_this_hour
    assert data['error_count'] == proxy.error_count
    assert data['created_at'] == proxy.created_at.isoformat()
    assert data['updated_at'] == proxy.updated_at.isoformat()

def test_cascade_delete(db_session):
    """Test cascade delete of sessions"""
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

    # Delete proxy
    db_session.delete(proxy)
    db_session.commit()

    # Session should be deleted
    assert db_session.query(Session).filter_by(proxy_id=proxy.id).first() is None

def test_proxy_string_representation(db_session):
    """Test string representation of proxy"""
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        username='test_user',
        password='test_pass'
    )
    assert str(proxy) == '192.168.1.1:8080:test_user:test_pass'
    assert repr(proxy) == '<Proxy 192.168.1.1:8080>'
