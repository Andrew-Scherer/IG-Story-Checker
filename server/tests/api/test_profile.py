"""
Profile API Tests
Tests for profile management endpoints
"""

import pytest
from flask import json
from models import Profile

def test_get_profiles_empty(client):
    """Should return empty list when no profiles exist"""
    response = client.get('/api/profiles')
    assert response.status_code == 200
    assert response.json == []

def test_create_profile(client, create_niche):
    """Should create new profile with valid data"""
    # Create niche first
    niche = create_niche('Fitness')
    
    data = {
        'username': 'testuser',
        'niche_id': niche.id
    }
    
    response = client.post('/api/profiles', json=data)
    assert response.status_code == 201
    
    profile = response.json
    assert profile['username'] == data['username']
    assert profile['niche_id'] == data['niche_id']
    assert profile['status'] == 'active'
    assert 'id' in profile
    assert 'url' in profile
    assert 'created_at' in profile

def test_create_profile_duplicate_username(client):
    """Should reject duplicate usernames"""
    data = {'username': 'testuser'}
    
    # Create first profile
    client.post('/api/profiles', json=data)
    
    # Try to create duplicate
    response = client.post('/api/profiles', json=data)
    assert response.status_code == 400
    assert 'already exists' in response.json['message'].lower()

def test_create_profile_invalid_niche(client):
    """Should reject non-existent niche ID"""
    data = {
        'username': 'testuser',
        'niche_id': 'nonexistent'
    }
    
    response = client.post('/api/profiles', json=data)
    assert response.status_code == 400
    assert 'invalid niche' in response.json['message'].lower()

def test_get_profile(client, create_profile):
    """Should return specific profile by ID"""
    # Create profile
    profile = create_profile('testuser')
    
    response = client.get(f'/api/profiles/{profile.id}')
    assert response.status_code == 200
    assert response.json['id'] == profile.id
    assert response.json['username'] == profile.username

def test_get_profile_not_found(client):
    """Should return 404 for non-existent profile"""
    response = client.get('/api/profiles/nonexistent')
    assert response.status_code == 404

def test_update_profile(client, create_niche, create_profile):
    """Should update existing profile"""
    # Create profile and new niche
    profile = create_profile('testuser')
    niche = create_niche('Fitness')
    
    update_data = {
        'niche_id': niche.id,
        'status': 'deleted'
    }
    
    response = client.put(f'/api/profiles/{profile.id}', json=update_data)
    assert response.status_code == 200
    assert response.json['niche_id'] == niche.id
    assert response.json['status'] == 'deleted'

def test_delete_profile(client, create_profile):
    """Should delete existing profile"""
    profile = create_profile('testuser')
    
    response = client.delete(f'/api/profiles/{profile.id}')
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f'/api/profiles/{profile.id}')
    assert get_response.status_code == 404

def test_bulk_delete_profiles(client, create_profile):
    """Should delete multiple profiles"""
    # Create profiles
    profiles = [
        create_profile('user1'),
        create_profile('user2'),
        create_profile('user3')
    ]
    profile_ids = [p.id for p in profiles]
    
    response = client.post('/api/profiles/bulk-delete', json={'ids': profile_ids})
    assert response.status_code == 200
    assert response.json['deleted'] == len(profile_ids)
    
    # Verify all deleted
    for profile_id in profile_ids:
        get_response = client.get(f'/api/profiles/{profile_id}')
        assert get_response.status_code == 404

def test_bulk_update_niche(client, create_niche, create_profile):
    """Should update niche for multiple profiles"""
    # Create profiles and new niche
    profiles = [
        create_profile('user1'),
        create_profile('user2')
    ]
    niche = create_niche('Fitness')
    profile_ids = [p.id for p in profiles]
    
    response = client.post('/api/profiles/bulk-update', json={
        'ids': profile_ids,
        'niche_id': niche.id
    })
    assert response.status_code == 200
    assert response.json['updated'] == len(profile_ids)
    
    # Verify updates
    for profile_id in profile_ids:
        get_response = client.get(f'/api/profiles/{profile_id}')
        assert get_response.json['niche_id'] == niche.id

def test_import_profiles(client, create_niche):
    """Should import profiles from username list"""
    niche = create_niche('Fitness')
    usernames = ['user1', 'user2', 'user3']
    
    response = client.post('/api/profiles/import', json={
        'usernames': usernames,
        'niche_id': niche.id
    })
    assert response.status_code == 200
    assert response.json['imported'] == len(usernames)
    assert response.json['skipped'] == 0
    
    # Verify all imported
    for username in usernames:
        profile = Profile.query.filter_by(username=username).first()
        assert profile is not None
        assert profile.niche_id == niche.id

def test_import_profiles_skip_duplicates(client, create_profile):
    """Should skip existing usernames during import"""
    # Create existing profile
    existing = create_profile('existing_user')
    
    usernames = ['existing_user', 'new_user']
    
    response = client.post('/api/profiles/import', json={
        'usernames': usernames
    })
    assert response.status_code == 200
    assert response.json['imported'] == 1  # Only new_user
    assert response.json['skipped'] == 1   # existing_user

def test_filter_profiles(client, create_niche, create_profile):
    """Should filter profiles by criteria"""
    # Create test data
    niche = create_niche('Fitness')
    create_profile('user1', niche_id=niche.id)
    create_profile('user2', niche_id=niche.id)
    create_profile('user3')  # No niche
    
    # Test niche filter
    response = client.get(f'/api/profiles?niche_id={niche.id}')
    assert response.status_code == 200
    assert len(response.json) == 2
    
    # Test status filter
    response = client.get('/api/profiles?status=active')
    assert response.status_code == 200
    assert len(response.json) == 3
    
    # Test search
    response = client.get('/api/profiles?search=user1')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['username'] == 'user1'
