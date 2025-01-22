"""
Test proxy API endpoints
"""
import pytest
from models.proxy import Proxy
from models.session import Session

def test_list_proxies(client, db_session):
    """Test GET /api/proxies"""
    # Create test proxies
    proxies = []
    for i in range(3):
        proxy = Proxy(
            ip=f'192.168.1.{i}',
            port=8080 + i,
            username=f'user_{i}',
            password=f'pass_{i}',
            is_active=True,
            total_requests=i * 10,
            failed_requests=i,
            requests_this_hour=i * 2,
            error_count=0
        )
        db_session.add(proxy)
        
        # Add session for each proxy
        session = Session(
            proxy=proxy,
            session=f'session_{i}',
            status=Session.STATUS_ACTIVE
        )
        db_session.add(session)
        proxies.append(proxy)
    
    db_session.commit()
    
    # Test endpoint
    response = client.get('/api/proxies')
    assert response.status_code == 200
    data = response.json
    
    # Verify response
    assert len(data) == 3
    for i, proxy_data in enumerate(data):
        proxy = proxies[i]
        assert proxy_data['ip'] == proxy.ip
        assert proxy_data['port'] == proxy.port
        assert proxy_data['username'] == proxy.username
        assert proxy_data['password'] == proxy.password
        assert proxy_data['is_active'] == proxy.is_active
        assert proxy_data['total_requests'] == proxy.total_requests
        assert proxy_data['failed_requests'] == proxy.failed_requests
        assert proxy_data['requests_this_hour'] == proxy.requests_this_hour
        assert proxy_data['error_count'] == proxy.error_count
        assert len(proxy_data['sessions']) == 1
        assert proxy_data['sessions'][0]['session'] == f'session_{i}'
        assert proxy_data['sessions'][0]['status'] == Session.STATUS_ACTIVE

def test_create_proxy(client, db_session):
    """Test POST /api/proxies"""
    # Test data
    proxy_data = {
        'ip': '192.168.1.1',
        'port': 8080,
        'username': 'test_user',
        'password': 'test_pass',
        'session': 'test_session'
    }
    
    # Test endpoint
    response = client.post('/api/proxies', json=proxy_data)
    assert response.status_code == 201
    data = response.json
    
    # Verify response
    assert data['ip'] == proxy_data['ip']
    assert data['port'] == proxy_data['port']
    assert data['username'] == proxy_data['username']
    assert data['password'] == proxy_data['password']
    assert data['is_active'] is True
    assert data['total_requests'] == 0
    assert data['failed_requests'] == 0
    assert data['requests_this_hour'] == 0
    assert data['error_count'] == 0
    assert len(data['sessions']) == 1
    assert data['sessions'][0]['session'] == proxy_data['session']
    assert data['sessions'][0]['status'] == Session.STATUS_ACTIVE
    
    # Verify database
    proxy = db_session.get(Proxy, data['id'])
    assert proxy is not None
    assert proxy.ip == proxy_data['ip']
    assert proxy.port == proxy_data['port']
    assert len(proxy.sessions.all()) == 1
    assert proxy.sessions[0].session == proxy_data['session']

def test_create_proxy_validation(client):
    """Test proxy creation validation"""
    # Missing required fields
    response = client.post('/api/proxies', json={})
    assert response.status_code == 400
    assert response.json['error'] == 'validation_error'
    assert 'ip' in response.json['details']['missing_fields']
    assert 'port' in response.json['details']['missing_fields']
    assert 'session' in response.json['details']['missing_fields']
    
    # Invalid port
    response = client.post('/api/proxies', json={
        'ip': '192.168.1.1',
        'port': 'invalid',
        'username': 'user',
        'password': 'pass',
        'session': 'test'
    })
    assert response.status_code == 400
    assert response.json['error'] == 'invalid_request'

def test_create_duplicate_proxy(client, db_session):
    """Test creating duplicate proxy"""
    proxy_data = {
        'ip': '192.168.1.1',
        'port': 8080,
        'username': 'test_user',
        'password': 'test_pass',
        'session': 'test_session'
    }
    
    # Create first proxy
    response = client.post('/api/proxies', json=proxy_data)
    assert response.status_code == 201
    
    # Try to create duplicate
    response = client.post('/api/proxies', json=proxy_data)
    assert response.status_code == 409
    assert response.json['error'] == 'duplicate_proxy'

def test_delete_proxy(client, db_session):
    """Test DELETE /api/proxies/<id>"""
    # Create test proxy
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        username='test_user',
        password='test_pass',
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
    
    # Test endpoint
    response = client.delete(f'/api/proxies/{proxy.id}')
    assert response.status_code == 204
    
    # Verify database
    assert db_session.get(Proxy, proxy.id) is None
    assert db_session.query(Session).filter_by(proxy_id=proxy.id).first() is None

def test_delete_nonexistent_proxy(client):
    """Test deleting nonexistent proxy"""
    response = client.delete('/api/proxies/999')
    assert response.status_code == 404
    assert response.json['error'] == 'not_found'

def test_update_proxy_status(client, db_session):
    """Test PATCH /api/proxies/<id>/status"""
    # Create test proxy
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        username='test_user',
        password='test_pass',
        is_active=True
    )
    db_session.add(proxy)
    db_session.commit()
    
    # Test endpoint
    response = client.patch(f'/api/proxies/{proxy.id}/status', json={
        'status': 'disabled'
    })
    assert response.status_code == 200
    data = response.json
    
    # Verify response
    assert data['is_active'] is False
    
    # Verify database
    proxy = db_session.get(Proxy, proxy.id)
    assert proxy.is_active is False

def test_update_nonexistent_proxy_status(client):
    """Test updating nonexistent proxy status"""
    response = client.patch('/api/proxies/999/status', json={
        'status': 'disabled'
    })
    assert response.status_code == 404
    assert response.json['error'] == 'not_found'

def test_update_proxy_status_validation(client, db_session):
    """Test proxy status update validation"""
    # Create test proxy
    proxy = Proxy(
        ip='192.168.1.1',
        port=8080,
        is_active=True
    )
    db_session.add(proxy)
    db_session.commit()
    
    # Missing status field
    response = client.patch(f'/api/proxies/{proxy.id}/status', json={})
    assert response.status_code == 400
    assert response.json['error'] == 'missing_field'
