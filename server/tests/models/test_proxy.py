import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy.exc import IntegrityError
from models.proxy import Proxy, ProxyStatus
from models.session import Session

@pytest.fixture
def proxy(db_session):
    proxy = Proxy(
        ip="165.231.24.193",
        port=4444,
        username="andres",
        password="Andres2025"
    )
    db_session.add(proxy)
    db_session.commit()
    return proxy

def test_create_proxy(proxy):
    """Test basic proxy creation"""
    assert proxy.id is not None
    assert proxy.ip == "165.231.24.193"
    assert proxy.port == 4444
    assert proxy.username == "andres"
    assert proxy.password == "Andres2025"
    assert proxy.status == ProxyStatus.ACTIVE

def test_proxy_required_fields(db_session):
    """Test required fields validation"""
    proxy = Proxy()
    db_session.add(proxy)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_proxy_string_representation(proxy):
    """Test string representation"""
    assert str(proxy) == "165.231.24.193:4444:andres:Andres2025"

def test_proxy_session_management(db_session, proxy):
    """Test one session per proxy rule"""
    # Add first session
    session1 = Session(
        session="sessionid=abc123;ds_user_id=12345;",
        proxy=proxy
    )
    db_session.add(session1)
    db_session.commit()
    
    assert len(proxy.sessions) == 1
    assert proxy.sessions[0] == session1
    
    # Try to add second session
    session2 = Session(
        session="sessionid=xyz789;ds_user_id=67890;",
        proxy=proxy
    )
    db_session.add(session2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_proxy_status_management(db_session, proxy):
    """Test proxy status transitions"""
    # Start as active
    assert proxy.status == ProxyStatus.ACTIVE
    assert proxy.is_usable
    
    # Mark as rate limited
    proxy.set_rate_limited()
    db_session.commit()
    assert proxy.status == ProxyStatus.RATE_LIMITED
    assert not proxy.is_usable
    assert proxy.cooldown_until > datetime.now(UTC)
    
    # Clear rate limit after cooldown
    proxy.cooldown_until = datetime.now(UTC) - timedelta(minutes=1)
    assert proxy.is_usable
    assert proxy.status == ProxyStatus.ACTIVE

def test_proxy_request_tracking(db_session, proxy):
    """Test request and error tracking"""
    # Record some requests
    proxy.record_request(success=True, response_time=150)
    proxy.record_request(success=True, response_time=200)
    proxy.record_request(success=False, error="Connection failed")
    db_session.commit()
    
    assert proxy.total_requests == 3
    assert proxy.failed_requests == 1
    assert abs(proxy.success_rate - 0.67) < 0.01  # Allow small floating point difference
    assert 170 <= proxy.average_response_time <= 180
    
    # Check error tracking
    assert proxy.last_error == "Connection failed"
    assert proxy.error_count == 1
    
    # Test error threshold
    for _ in range(4):
        proxy.record_request(success=False, error="Connection failed")
    db_session.commit()
    
    assert proxy.status == ProxyStatus.DISABLED
    assert not proxy.is_usable

def test_proxy_request_tracking_metrics(db_session, proxy):
    """Test request tracking metrics"""
    # Record some requests
    for _ in range(10):
        proxy.record_request(success=True, response_time=100)
    db_session.commit()
    
    assert proxy.requests_this_hour == 10  # Tracks total requests in current period
    assert proxy.last_reset is not None  # Timestamp is updated
    assert proxy.last_used > datetime.now(UTC) - timedelta(minutes=1)

def test_proxy_rate_limit_handling(db_session, proxy):
    """Test rate limit detection and cooldown"""
    # Add requests up to limit
    for _ in range(proxy.HOURLY_LIMIT):
        proxy.record_request(success=True, response_time=100)
    db_session.commit()
    
    assert proxy.requests_this_hour == proxy.HOURLY_LIMIT
    assert proxy.status == ProxyStatus.RATE_LIMITED
    assert not proxy.is_usable
    
    # Check cooldown period
    assert proxy.cooldown_until > datetime.now(UTC)
    original_cooldown = proxy.cooldown_until
    
    # Additional rate limits extend cooldown
    proxy.set_rate_limited()
    assert proxy.cooldown_until > original_cooldown
