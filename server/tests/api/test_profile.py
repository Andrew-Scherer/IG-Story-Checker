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

@pytest.mark.usefixtures("db_session")
def test_list_profiles(client):
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

@pytest.mark.usefixtures("db_session")
def test_create_profile(client):
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

@pytest.mark.usefixtures("db_session")
def test_bulk_create_profiles(client):
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

@pytest.mark.usefixtures("db_session")
def test_get_profile(client):
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

@pytest.mark.usefixtures("db_session")
def test_update_profile(client):
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

@pytest.mark.usefixtures("db_session")
def test_delete_profile(client):
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

@pytest.mark.usefixtures("db_session")
def test_reactivate_profile(client):
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

@pytest.mark.usefixtures("db_session")
def test_record_check(client):
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

@pytest.mark.usefixtures("db_session")
def test_sort_profiles_by_niche(client, db_session):
    """Test sorting profiles by niche"""
    print("\n--- Starting test_sort_profiles_by_niche ---")

    # Create test niches
    niche1 = client.post('/api/niches', json={'name': 'Niche A'}).get_json()
    niche2 = client.post('/api/niches', json={'name': 'Niche B'}).get_json()
    niche3 = client.post('/api/niches', json={'name': 'Niche C'}).get_json()
    print(f"Created niches: {niche1}, {niche2}, {niche3}")

    # Create test profiles with different niches
    profiles = [
        {'username': 'user1', 'niche_id': niche2['id']},
        {'username': 'user2', 'niche_id': niche1['id']},
        {'username': 'user3', 'niche_id': niche3['id']},
        {'username': 'user4', 'niche_id': niche2['id']}
    ]
    for profile in profiles:
        response = client.post('/api/profiles', json=profile)
        print(f"Created profile: {response.get_json()}")

    # Commit the changes to the database
    db_session.commit()

    # Verify profiles in database
    from models.profile import Profile
    db_profiles = db_session.query(Profile).all()
    print(f"Profiles in database: {[(p.username, p.niche_id) for p in db_profiles]}")

    # Clear the session to ensure fresh data is loaded
    db_session.expunge_all()

    # Test sorting by niche in ascending order
    response = client.get('/api/profiles?sort_by=niche__name&sort_direction=asc')
    assert response.status_code == 200
    data = json.loads(response.data)
    profiles = data['profiles']
    print(f"Sorted profiles (asc): {[(p['username'], p['niche__name']) for p in profiles]}")
    assert [p['niche__name'] for p in profiles] == ['Niche A', 'Niche B', 'Niche B', 'Niche C']
    assert [p['username'] for p in profiles] == ['user2', 'user1', 'user4', 'user3']

    # Test sorting by niche in descending order
    response = client.get('/api/profiles?sort_by=niche__name&sort_direction=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    profiles = data['profiles']
    print(f"Sorted profiles (desc): {[(p['username'], p['niche__name']) for p in profiles]}")
    assert [p['niche__name'] for p in profiles] == ['Niche C', 'Niche B', 'Niche B', 'Niche A']
    assert [p['username'] for p in profiles] == ['user3', 'user1', 'user4', 'user2']

    print("--- Finished test_sort_profiles_by_niche ---")
