"""
Test Profile Creation
Focused tests for profile creation functionality
"""

import pytest
import json
from datetime import datetime, UTC

def test_direct_profile_creation(db_session):
    """Test creating a profile directly with SQLAlchemy"""
    from models.profile import Profile
    
    print("\n=== Testing direct profile creation ===")
    
    # Create profile object
    profile = Profile(
        username='test_direct_user',
        status='active',
        niche_id=None
    )
    print(f"Created profile object: {profile}")
    
    # Add to session
    print("Adding to session")
    db_session.add(profile)
    
    # Commit
    print("Committing to database")
    db_session.commit()
    print("Commit successful")
    
    # Verify profile was created
    saved_profile = db_session.query(Profile).filter_by(username='test_direct_user').first()
    assert saved_profile is not None
    assert saved_profile.username == 'test_direct_user'
    assert saved_profile.status == 'active'

def test_api_profile_creation(client, db_session):
    """Test creating a profile through the API"""
    from models.profile import Profile
    print("\n=== Testing API profile creation ===")
    
    # Create profile through API
    data = {
        'username': 'test_api_user',
        'status': 'active',
        'niche_id': None
    }
    print(f"Sending POST request with data: {data}")
    
    response = client.post('/api/profiles', json=data)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    
    assert response.status_code == 201
    
    # Verify response structure
    response_data = json.loads(response.data)
    assert response_data['username'] == 'test_api_user'
    assert response_data['status'] == 'active'
    assert 'id' in response_data
    
    # Verify profile was created in database
    profile = db_session.query(Profile).filter_by(username='test_api_user').first()
    assert profile is not None
    assert profile.username == 'test_api_user'
    assert profile.status == 'active'

def test_profile_creation_with_niche(client, db_session):
    """Test creating a profile with an associated niche"""
    from models.profile import Profile
    print("\n=== Testing profile creation with niche ===")
    
    # First create a niche
    niche_response = client.post('/api/niches', json={'name': 'Test Niche'})
    assert niche_response.status_code == 201
    niche_data = json.loads(niche_response.data)
    niche_id = niche_data['id']
    print(f"Created niche with ID: {niche_id}")
    
    # Create profile with niche
    profile_data = {
        'username': 'test_niche_user',
        'status': 'active',
        'niche_id': niche_id
    }
    print(f"Creating profile with data: {profile_data}")
    
    response = client.post('/api/profiles', json=profile_data)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    
    assert response.status_code == 201
    
    # Verify profile was created with correct niche
    profile = db_session.query(Profile).filter_by(username='test_niche_user').first()
    assert profile is not None
    assert profile.niche_id == niche_id

def test_file_import_profile_creation(client, db_session):
    """Test creating a profile through file import process"""
    print("\n=== Testing file import profile creation ===")
    
    # Simulate the data structure from profileStore.js importFromFile
    data = {
        'username': '_be100withmeshorty_',
        'status': 'active',
        'niche_id': 1
    }
    print(f"Simulating file import with data: {data}")
    
    # Create niche first
    niche_response = client.post('/api/niches', json={'name': 'Test Niche'})
    assert niche_response.status_code == 201
    niche_data = json.loads(niche_response.data)
    niche_id = niche_data['id']
    print(f"Created niche with ID: {niche_id}")
    
    # Update data with actual niche ID
    data['niche_id'] = niche_id
    print(f"Updated data with niche ID: {data}")
    
    # Attempt profile creation
    response = client.post('/api/profiles', json=data)
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    
    assert response.status_code == 201
    
    # Verify response structure
    response_data = json.loads(response.data)
    assert response_data['username'] == '_be100withmeshorty_'
    assert response_data['status'] == 'active'
    assert response_data['niche_id'] == niche_id
    
    # Verify profile was created in database
    from models.profile import Profile
    profile = db_session.query(Profile).filter_by(username='_be100withmeshorty_').first()
    assert profile is not None
    assert profile.username == '_be100withmeshorty_'
    assert profile.status == 'active'
    assert profile.niche_id == niche_id

def test_profile_creation_validation(client, db_session):
    """Test profile creation validation rules"""
    print("\n=== Testing profile creation validation ===")
    
    # Test duplicate username
    print("Testing duplicate username")
    data = {'username': 'duplicate_user', 'status': 'active'}
    
    # Create first profile
    response = client.post('/api/profiles', json=data)
    assert response.status_code == 201
    
    # Try to create duplicate
    response = client.post('/api/profiles', json=data)
    print(f"Duplicate creation response: {response.status_code}")
    print(f"Error message: {response.data}")
    assert response.status_code == 400
    assert b'already exists' in response.data
    
    # Test empty username
    print("Testing empty username")
    response = client.post('/api/profiles', json={'username': '', 'status': 'active'})
    print(f"Empty username response: {response.status_code}")
    print(f"Error message: {response.data}")
    assert response.status_code == 400
    assert b'cannot be empty' in response.data
    
    # Test invalid status
    print("Testing invalid status")
    response = client.post('/api/profiles', json={
        'username': 'status_test',
        'status': 'invalid_status'
    })
    print(f"Invalid status response: {response.status_code}")
    print(f"Error message: {response.data}")
    assert response.status_code == 400
    assert b'Invalid status' in response.data

def test_profile_file_import_with_variations(client, db_session):
    """Test importing profiles from file with various username variations"""
    print("\n=== Testing profile file import with variations ===")
    
    # Create a test niche
    niche_response = client.post('/api/niches', json={'name': 'Test Import Niche'})
    assert niche_response.status_code == 201
    niche_id = json.loads(niche_response.data)['id']
    
    # Create test file content with username variations
    test_profiles = [
        'test_user_1',
        'test.user.1',  # Similar to test_user_1
        'Test_User_1',  # Case variation
        'https://instagram.com/test_user_1',  # URL format
        'unique_user_1',
        'profile_123',
        'profile.123'   # Similar to profile_123
    ]
    
    # Convert profiles to file-like object
    from io import BytesIO
    file_content = '\n'.join(test_profiles).encode('utf-8')
    file_obj = BytesIO(file_content)
    file_obj.name = 'test_profiles.txt'
    
    # Import profiles
    response = client.post(
        f'/api/profiles/niches/{niche_id}/import',
        data={'file': (file_obj, 'test_profiles.txt')},
        content_type='multipart/form-data'
    )
    
    print(f"Import response status: {response.status_code}")
    print(f"Import response data: {response.data}")
    
    assert response.status_code in [201, 207]  # 207 for partial success
    
    response_data = json.loads(response.data)
    print("\nCreated profiles:", len(response_data['created']))
    print("Errors:", len(response_data['errors']))
    
    # Analyze duplicate detection
    duplicate_errors = [
        error for error in response_data['errors']
        if error['error'] == 'Profile already exists'
    ]
    print("\nDuplicate errors:", len(duplicate_errors))
    for error in duplicate_errors:
        print(f"Duplicate detected: {error['line']}")
    
    # Verify profiles in database
    from models.profile import Profile
    db_profiles = db_session.query(Profile).all()
    print("\nProfiles in database:", len(db_profiles))
    for profile in db_profiles:
        print(f"- {profile.username}")
    
    # Test retrieving profiles through API
    list_response = client.get('/api/profiles')
    assert list_response.status_code == 200
    list_data = json.loads(list_response.data)
    print("\nProfiles returned by API:", len(list_data['profiles']))
    
    # Verify the number of unique usernames matches the number of profiles
    unique_usernames = {profile['username'].lower() for profile in list_data['profiles']}
    print(f"\nUnique usernames in database: {len(unique_usernames)}")
    print("Usernames:", unique_usernames)
