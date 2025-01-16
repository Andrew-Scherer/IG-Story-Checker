"""
Settings API Tests
Tests for system settings and proxy management endpoints
"""

import pytest
from models import SystemSettings, Proxy

def test_get_system_settings(client):
    """Should return current system settings"""
    response = client.get('/api/settings/system')
    assert response.status_code == 200
    
    settings = response.json
    assert 'profiles_per_minute' in settings
    assert 'max_threads' in settings
    assert 'default_batch_size' in settings
    assert 'story_retention_hours' in settings
    assert 'auto_trigger_enabled' in settings

def test_update_system_settings(client):
    """Should update system settings"""
    updates = {
        'profiles_per_minute': 50,
        'max_threads': 5,
        'default_batch_size': 200,
        'story_retention_hours': 48,
        'auto_trigger_enabled': False
    }
    
    response = client.put('/api/settings/system', json=updates)
    assert response.status_code == 200
    
    settings = response.json
    for key, value in updates.items():
        assert settings[key] == value

def test_update_invalid_settings(client):
    """Should reject invalid setting values"""
    invalid_updates = {
        'profiles_per_minute': -1,  # Invalid: negative
        'max_threads': 0,           # Invalid: zero
        'story_retention_hours': 0  # Invalid: zero
    }
    
    response = client.put('/api/settings/system', json=invalid_updates)
    assert response.status_code == 400
    assert 'invalid' in response.json['message'].lower()

def test_get_proxies_empty(client):
    """Should return empty list when no proxies exist"""
    response = client.get('/api/settings/proxies')
    assert response.status_code == 200
    assert response.json == []

def test_add_proxy(client):
    """Should add new proxy with valid data"""
    data = {
        'host': '127.0.0.1',
        'port': 8080,
        'username': 'user',
        'password': 'pass'
    }
    
    response = client.post('/api/settings/proxies', json=data)
    assert response.status_code == 201
    
    proxy = response.json
    assert proxy['host'] == data['host']
    assert proxy['port'] == data['port']
    assert proxy['username'] == data['username']
    assert proxy['is_active'] is True
    assert 'id' in proxy

def test_add_proxy_invalid_data(client):
    """Should reject invalid proxy data"""
    invalid_data = [
        {'host': '127.0.0.1'},  # Missing port
        {'port': 8080},         # Missing host
        {'host': '127.0.0.1', 'port': -1},  # Invalid port
        {'host': '', 'port': 8080}          # Empty host
    ]
    
    for data in invalid_data:
        response = client.post('/api/settings/proxies', json=data)
        assert response.status_code == 400

def test_update_proxy(client, create_proxy):
    """Should update existing proxy"""
    proxy = create_proxy('127.0.0.1', 8080)
    
    updates = {
        'host': '127.0.0.2',
        'port': 8081,
        'username': 'newuser',
        'password': 'newpass',
        'is_active': False
    }
    
    response = client.put(f'/api/settings/proxies/{proxy.id}', json=updates)
    assert response.status_code == 200
    
    updated = response.json
    for key, value in updates.items():
        assert updated[key] == value

def test_delete_proxy(client, create_proxy):
    """Should delete existing proxy"""
    proxy = create_proxy('127.0.0.1', 8080)
    
    response = client.delete(f'/api/settings/proxies/{proxy.id}')
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f'/api/settings/proxies/{proxy.id}')
    assert get_response.status_code == 404

def test_test_proxy(client, create_proxy):
    """Should test proxy connection"""
    proxy = create_proxy('127.0.0.1', 8080)
    
    response = client.post(f'/api/settings/proxies/{proxy.id}/test')
    assert response.status_code == 200
    assert 'is_working' in response.json
    assert 'error' in response.json

def test_bulk_test_proxies(client, create_proxy):
    """Should test multiple proxies"""
    proxies = [
        create_proxy('127.0.0.1', 8080),
        create_proxy('127.0.0.2', 8081)
    ]
    
    response = client.post('/api/settings/proxies/test-all')
    assert response.status_code == 200
    assert len(response.json['results']) == 2
    assert all('is_working' in r for r in response.json['results'])

def test_get_proxy_stats(client, create_proxy):
    """Should return proxy usage statistics"""
    proxy = create_proxy('127.0.0.1', 8080)
    
    response = client.get(f'/api/settings/proxies/{proxy.id}/stats')
    assert response.status_code == 200
    assert 'total_requests' in response.json
    assert 'failed_requests' in response.json
    assert 'average_response_time' in response.json

def test_rotate_proxies(client, create_proxy):
    """Should rotate active proxies"""
    # Create some active and inactive proxies
    active1 = create_proxy('127.0.0.1', 8080)
    active2 = create_proxy('127.0.0.2', 8081)
    inactive = create_proxy('127.0.0.3', 8082)
    inactive.is_active = False
    inactive.save()
    
    response = client.post('/api/settings/proxies/rotate')
    assert response.status_code == 200
    assert response.json['rotated'] == 2  # Only active proxies
