"""
Niche API Tests
Tests for niche management endpoints
"""

import pytest
from flask import json
from models import Niche

def test_get_niches_empty(client):
    """Should return empty list when no niches exist"""
    response = client.get('/api/niches')
    assert response.status_code == 200
    assert response.json == []

def test_create_niche(client):
    """Should create new niche with valid data"""
    data = {
        'name': 'Fitness',
        'daily_story_target': 20,
        'description': 'Fitness and wellness profiles'
    }
    
    response = client.post('/api/niches', json=data)
    assert response.status_code == 201
    
    niche = response.json
    assert niche['name'] == data['name']
    assert niche['daily_story_target'] == data['daily_story_target']
    assert niche['description'] == data['description']
    assert 'id' in niche
    assert 'created_at' in niche

def test_create_niche_duplicate_name(client):
    """Should reject duplicate niche names"""
    data = {'name': 'Fitness'}
    
    # Create first niche
    client.post('/api/niches', json=data)
    
    # Try to create duplicate
    response = client.post('/api/niches', json=data)
    assert response.status_code == 400
    assert 'already exists' in response.json['message'].lower()

def test_get_niche(client):
    """Should return specific niche by ID"""
    # Create niche
    data = {'name': 'Fitness'}
    create_response = client.post('/api/niches', json=data)
    niche_id = create_response.json['id']
    
    # Get niche
    response = client.get(f'/api/niches/{niche_id}')
    assert response.status_code == 200
    assert response.json['id'] == niche_id
    assert response.json['name'] == data['name']

def test_get_niche_not_found(client):
    """Should return 404 for non-existent niche"""
    response = client.get('/api/niches/nonexistent')
    assert response.status_code == 404

def test_update_niche(client):
    """Should update existing niche"""
    # Create niche
    create_data = {'name': 'Fitness'}
    create_response = client.post('/api/niches', json=create_data)
    niche_id = create_response.json['id']
    
    # Update niche
    update_data = {
        'name': 'Health & Fitness',
        'daily_story_target': 25,
        'description': 'Updated description'
    }
    response = client.put(f'/api/niches/{niche_id}', json=update_data)
    assert response.status_code == 200
    assert response.json['name'] == update_data['name']
    assert response.json['daily_story_target'] == update_data['daily_story_target']
    assert response.json['description'] == update_data['description']

def test_delete_niche(client):
    """Should delete existing niche"""
    # Create niche
    data = {'name': 'Fitness'}
    create_response = client.post('/api/niches', json=data)
    niche_id = create_response.json['id']
    
    # Delete niche
    response = client.delete(f'/api/niches/{niche_id}')
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f'/api/niches/{niche_id}')
    assert get_response.status_code == 404

def test_reorder_niches(client):
    """Should reorder niches based on provided order"""
    # Create niches
    niches = []
    for name in ['Fitness', 'Fashion', 'Food']:
        response = client.post('/api/niches', json={'name': name})
        niches.append(response.json)
    
    # Reorder niches
    new_order = [niches[2]['id'], niches[0]['id'], niches[1]['id']]
    response = client.post('/api/niches/reorder', json={'order': new_order})
    assert response.status_code == 200
    
    # Verify new order
    response = client.get('/api/niches')
    assert response.status_code == 200
    assert [n['id'] for n in response.json] == new_order

def test_get_niche_profiles(client):
    """Should return profiles for specific niche"""
    # Create niche
    niche_response = client.post('/api/niches', json={'name': 'Fitness'})
    niche_id = niche_response.json['id']
    
    # Create profiles (using profile API)
    profiles = [
        {'username': 'user1', 'niche_id': niche_id},
        {'username': 'user2', 'niche_id': niche_id}
    ]
    for profile in profiles:
        client.post('/api/profiles', json=profile)
    
    # Get niche profiles
    response = client.get(f'/api/niches/{niche_id}/profiles')
    assert response.status_code == 200
    assert len(response.json) == 2
    assert all(p['niche_id'] == niche_id for p in response.json)

def test_get_niche_stats(client):
    """Should return statistics for specific niche"""
    # Create niche
    niche_response = client.post('/api/niches', json={'name': 'Fitness'})
    niche_id = niche_response.json['id']
    
    response = client.get(f'/api/niches/{niche_id}/stats')
    assert response.status_code == 200
    assert 'total_profiles' in response.json
    assert 'active_profiles' in response.json
    assert 'current_stories' in response.json
