"""
Settings API Tests
Tests for system settings endpoints
"""

import pytest
from models import SystemSettings

def test_get_settings(client):
    """Should return current system settings"""
    response = client.get('/api/settings')
    assert response.status_code == 200
    
    settings = response.json
    assert 'profiles_per_minute' in settings
    assert 'max_threads' in settings
    assert 'default_batch_size' in settings
    assert 'story_retention_hours' in settings
    assert 'auto_trigger_enabled' in settings
    assert 'min_trigger_interval' in settings
    assert 'proxy_test_timeout' in settings
    assert 'proxy_max_failures' in settings
    assert 'proxy_hourly_limit' in settings
    assert 'notifications_enabled' in settings

def test_update_settings(client):
    """Should update system settings"""
    new_settings = {
        'profiles_per_minute': 50,
        'max_threads': 5,
        'default_batch_size': 200,
        'story_retention_hours': 48,
        'auto_trigger_enabled': False,
        'min_trigger_interval': 120,
        'proxy_test_timeout': 20,
        'proxy_max_failures': 5,
        'proxy_hourly_limit': 200,
        'notifications_enabled': False,
        'notification_email': 'test@example.com'
    }
    
    response = client.put('/api/settings', json=new_settings)
    assert response.status_code == 200
    
    # Verify settings were updated
    settings = SystemSettings.get_settings()
    for key, value in new_settings.items():
        assert getattr(settings, key) == value

def test_update_settings_validation(client):
    """Should validate settings updates"""
    invalid_settings = {
        'profiles_per_minute': -1,  # Cannot be negative
        'max_threads': 0,  # Must be positive
        'default_batch_size': 1000000,  # Too large
        'notification_email': 'invalid-email'  # Invalid email format
    }
    
    response = client.put('/api/settings', json=invalid_settings)
    assert response.status_code == 400
    assert 'validation errors' in response.json['message'].lower()
