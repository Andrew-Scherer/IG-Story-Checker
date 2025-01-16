"""
Test Profile API
Tests API endpoints for profile management
"""

import pytest
import json
from datetime import datetime, timedelta, UTC

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def test_list_profiles(client, db_session):
    """Test GET /api/profiles"""
    # Create test profiles
    profiles = [
        {'username': 'user1', 'status': 'active'},
        {'username': 'user2', 'status': 'active'},
        {'username': 'user3', 'status': 'suspended'}
    ]
    
    for profile in profiles:
        response = client.post('/api/profiles', json=profile)
        assert response.status_code == 201
    
    # Test basic listing
    response = client.get('/api/profiles')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 3
    
    # Verify response structure
    profile = data[0]
    assert set(profile.keys()) == {
        'id', 'username', 'url', 'niche_id', 'status',
        'total_checks', 'total_detections', 'detection_rate',
        'last_checked', 'last_detected',
        'created_at', 'updated_at', 'deleted_at'
    }
    
    # Test filtering by status
    response = client.get('/api/profiles?status=active')
    data = json.loads(response.data)
    assert len(data) == 2
    assert all(p['status'] == 'active' for p in data)
    
    # Test filtering by niche
    response = client.post('/api/niches', json={'name': 'Test Niche'})
    print("\nNiche creation response:", response.data)
    niche_id = json.loads(response.data)['id']
    
    response = client.post('/api/profiles', json={
        'username': 'niche_user',
        'niche_id': niche_id
    })
    print("\nProfile creation response:", response.data)
    assert response.status_code == 201
    
    # Verify profile was created with correct niche_id
    created_profile = json.loads(response.data)
    print("\nCreated profile:", created_profile)
    assert created_profile['niche_id'] == niche_id
    
    response = client.get(f'/api/profiles?niche_id={niche_id}')
    print("\nProfile filter response:", response.data)
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['username'] == 'niche_user'

def test_create_profile(client, db_session):
    """Test POST /api/profiles"""
    # Test valid creation
    response = client.post('/api/profiles', json={
        'username': 'testuser',
        'url': 'https://instagram.com/testuser',
        'status': 'active'
    })
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert data['username'] == 'testuser'
    assert data['status'] == 'active'
    assert 'id' in data
    
    # Test duplicate username
    response = client.post('/api/profiles', json={
        'username': 'testuser'
    })
    assert response.status_code == 400
    assert b'already exists' in response.data
    
    # Test empty username
    response = client.post('/api/profiles', json={
        'username': ''
    })
    assert response.status_code == 400
    assert b'cannot be empty' in response.data
    
    # Test missing username
    response = client.post('/api/profiles', json={
        'url': 'https://instagram.com/missing'
    })
    assert response.status_code == 400
    assert b'username is required' in response.data
    
    # Test invalid status
    response = client.post('/api/profiles', json={
        'username': 'statustest',
        'status': 'invalid'
    })
    assert response.status_code == 400
    assert b'Invalid status' in response.data

def test_bulk_create_profiles(client, db_session):
    """Test POST /api/profiles/bulk"""
    profiles = [
        {'username': 'bulk1'},
        {'username': 'bulk2'},
        {'username': 'bulk3'}
    ]
    
    response = client.post('/api/profiles/bulk', json={
        'profiles': profiles
    })
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert len(data['created']) == 3
    assert len(data['errors']) == 0
    
    # Test with some invalid profiles
    profiles = [
        {'username': 'bulk4'},
        {'username': 'bulk1'},  # Duplicate
        {'username': ''},  # Empty
        {'username': 'bulk5'}
    ]
    
    response = client.post('/api/profiles/bulk', json={
        'profiles': profiles
    })
    assert response.status_code == 207  # Partial success
    
    data = json.loads(response.data)
    assert len(data['created']) == 2  # bulk4 and bulk5
    assert len(data['errors']) == 2  # bulk1 and empty

def test_get_profile(client, db_session):
    """Test GET /api/profiles/<id>"""
    # Create test profile
    response = client.post('/api/profiles', json={
        'username': 'gettest'
    })
    profile_id = json.loads(response.data)['id']
    
    # Get profile by ID
    response = client.get(f'/api/profiles/{profile_id}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['username'] == 'gettest'
    
    # Test invalid ID
    response = client.get('/api/profiles/999999')
    assert response.status_code == 404

def test_update_profile(client, db_session):
    """Test PUT /api/profiles/<id>"""
    # Create test profile
    response = client.post('/api/profiles', json={
        'username': 'updatetest'
    })
    profile_id = json.loads(response.data)['id']
    
    # Update profile
    response = client.put(f'/api/profiles/{profile_id}', json={
        'url': 'https://instagram.com/updated',
        'status': 'suspended'
    })
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['url'] == 'https://instagram.com/updated'
    assert data['status'] == 'suspended'
    
    # Test invalid status
    response = client.put(f'/api/profiles/{profile_id}', json={
        'status': 'invalid'
    })
    assert response.status_code == 400
    assert b'Invalid status' in response.data
    
    # Test invalid ID
    response = client.put('/api/profiles/999999', json={
        'status': 'active'
    })
    assert response.status_code == 404

def test_delete_profile(client, db_session):
    """Test DELETE /api/profiles/<id>"""
    # Create test profile
    response = client.post('/api/profiles', json={
        'username': 'deletetest'
    })
    profile_id = json.loads(response.data)['id']
    
    # Delete profile (soft delete)
    response = client.delete(f'/api/profiles/{profile_id}')
    assert response.status_code == 204
    
    # Verify soft deletion
    response = client.get(f'/api/profiles/{profile_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'deleted'
    assert data['deleted_at'] is not None
    
    # Test invalid ID
    response = client.delete('/api/profiles/999999')
    assert response.status_code == 404

def test_reactivate_profile(client, db_session):
    """Test POST /api/profiles/<id>/reactivate"""
    # Create and delete test profile
    response = client.post('/api/profiles', json={
        'username': 'reactivatetest'
    })
    profile_id = json.loads(response.data)['id']
    
    client.delete(f'/api/profiles/{profile_id}')
    
    # Reactivate profile
    response = client.post(f'/api/profiles/{profile_id}/reactivate')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'active'
    assert data['deleted_at'] is None
    
    # Test invalid ID
    response = client.post('/api/profiles/999999/reactivate')
    assert response.status_code == 404

def test_record_check(client, db_session):
    """Test POST /api/profiles/<id>/record_check"""
    # Create test profile
    response = client.post('/api/profiles', json={
        'username': 'checktest'
    })
    profile_id = json.loads(response.data)['id']
    
    # Record successful check
    response = client.post(f'/api/profiles/{profile_id}/record_check', json={
        'story_detected': True
    })
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['total_checks'] == 1
    assert data['total_detections'] == 1
    assert data['last_checked'] is not None
    assert data['last_detected'] is not None
    
    # Record unsuccessful check
    response = client.post(f'/api/profiles/{profile_id}/record_check', json={
        'story_detected': False
    })
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['total_checks'] == 2
    assert data['total_detections'] == 1
    assert data['detection_rate'] == 50.0
    
    # Test invalid ID
    response = client.post('/api/profiles/999999/record_check', json={
        'story_detected': True
    })
    assert response.status_code == 404
