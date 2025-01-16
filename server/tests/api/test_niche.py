"""
Test Niche API
Tests API endpoints for niche management
"""

import pytest
import json
from datetime import datetime

def test_list_niches(client, db_session):
    """Test GET /api/niches"""
    # Create test niches
    niches = [
        {'name': 'Fashion', 'display_order': 0},
        {'name': 'Travel', 'display_order': 1},
        {'name': 'Food', 'display_order': 2}
    ]
    
    for niche in niches:
        response = client.post('/api/niches', json=niche)
        assert response.status_code == 201
    
    # Get list of niches
    response = client.get('/api/niches')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 3
    assert data[0]['name'] == 'Fashion'
    assert data[1]['name'] == 'Travel'
    assert data[2]['name'] == 'Food'
    
    # Verify response structure
    niche = data[0]
    assert set(niche.keys()) == {
        'id', 'name', 'display_order', 'daily_story_target',
        'created_at', 'updated_at'
    }

def test_create_niche(client, db_session):
    """Test POST /api/niches"""
    # Test valid creation
    response = client.post('/api/niches', json={
        'name': 'Fitness',
        'display_order': 1
    })
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert data['name'] == 'Fitness'
    assert data['display_order'] == 1
    assert 'id' in data
    
    # Test duplicate name
    response = client.post('/api/niches', json={
        'name': 'Fitness'
    })
    assert response.status_code == 400
    assert b'already exists' in response.data
    
    # Test empty name
    response = client.post('/api/niches', json={
        'name': ''
    })
    assert response.status_code == 400
    assert b'cannot be empty' in response.data
    
    # Test missing name
    response = client.post('/api/niches', json={
        'display_order': 0
    })
    assert response.status_code == 400
    assert b'name is required' in response.data

def test_get_niche(client, db_session):
    """Test GET /api/niches/<id>"""
    # Create test niche
    response = client.post('/api/niches', json={
        'name': 'Gaming'
    })
    niche_id = json.loads(response.data)['id']
    
    # Get niche by ID
    response = client.get(f'/api/niches/{niche_id}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['name'] == 'Gaming'
    
    # Test invalid ID
    response = client.get('/api/niches/999999')
    assert response.status_code == 404

def test_update_niche(client, db_session):
    """Test PUT /api/niches/<id>"""
    # Create test niche
    response = client.post('/api/niches', json={
        'name': 'Art'
    })
    niche_id = json.loads(response.data)['id']
    
    # Update niche
    response = client.put(f'/api/niches/{niche_id}', json={
        'name': 'Digital Art',
        'display_order': 5
    })
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['name'] == 'Digital Art'
    assert data['display_order'] == 5
    
    # Test duplicate name
    client.post('/api/niches', json={'name': 'Photography'})
    response = client.put(f'/api/niches/{niche_id}', json={
        'name': 'Photography'
    })
    assert response.status_code == 400
    assert b'already exists' in response.data
    
    # Verify niche still exists
    verify = client.get(f'/api/niches/{niche_id}')
    assert verify.status_code == 200
    
    # Test empty name
    response = client.put(f'/api/niches/{niche_id}', json={
        'name': ''
    })
    assert response.status_code == 400
    assert b'cannot be empty' in response.data
    
    # Test invalid ID
    response = client.put('/api/niches/999999', json={
        'name': 'Invalid'
    })
    assert response.status_code == 404

def test_delete_niche(client, db_session):
    """Test DELETE /api/niches/<id>"""
    # Create test niche
    response = client.post('/api/niches', json={
        'name': 'Music'
    })
    niche_id = json.loads(response.data)['id']
    
    # Delete niche
    response = client.delete(f'/api/niches/{niche_id}')
    assert response.status_code == 204
    
    # Verify deletion
    response = client.get(f'/api/niches/{niche_id}')
    assert response.status_code == 404
    
    # Test invalid ID
    response = client.delete('/api/niches/999999')
    assert response.status_code == 404

def test_reorder_niches(client, db_session):
    """Test POST /api/niches/reorder"""
    # Create test niches
    niches = []
    for name in ['Tech', 'Science', 'Nature']:
        response = client.post('/api/niches', json={'name': name})
        niches.append(json.loads(response.data))
    
    # Reorder niches
    new_order = [niches[2]['id'], niches[0]['id'], niches[1]['id']]
    response = client.post('/api/niches/reorder', json={
        'niche_ids': new_order
    })
    assert response.status_code == 200
    
    # Verify new order
    response = client.get('/api/niches')
    data = json.loads(response.data)
    assert [n['id'] for n in data] == new_order
    
    # Test invalid ID in order
    response = client.post('/api/niches/reorder', json={
        'niche_ids': [*new_order, '999999']
    })
    assert response.status_code == 400
    assert b'Invalid niche ID' in response.data
    
    # Test missing niche ID
    partial_order = new_order[:-1]
    response = client.post('/api/niches/reorder', json={
        'niche_ids': partial_order
    })
    assert response.status_code == 400
    assert b'All niches must be included' in response.data
