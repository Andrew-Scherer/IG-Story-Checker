"""
Batch API Tests
Tests for batch processing endpoints
"""

import pytest
from datetime import datetime, timedelta
from models import Batch, BatchProfile, StoryResult

def test_get_batches_empty(client):
    """Should return empty list when no batches exist"""
    response = client.get('/api/batches')
    assert response.status_code == 200
    assert response.json == []

def test_create_batch(client, create_niche, create_profile):
    """Should create new batch with valid data"""
    # Create niche and profiles
    niche = create_niche('Fitness')
    for i in range(5):
        create_profile(f'user{i}', niche_id=niche.id)
    
    data = {
        'niche_id': niche.id,
        'profile_count': 3
    }
    
    response = client.post('/api/batches', json=data)
    assert response.status_code == 201
    
    batch = response.json
    assert batch['niche_id'] == niche.id
    assert batch['status'] == 'pending'
    assert batch['total_profiles'] == 3
    assert 'id' in batch

def test_create_batch_invalid_niche(client):
    """Should reject batch creation for non-existent niche"""
    data = {
        'niche_id': 'nonexistent',
        'profile_count': 10
    }
    
    response = client.post('/api/batches', json=data)
    assert response.status_code == 400
    assert 'invalid niche' in response.json['message'].lower()

def test_create_batch_niche_in_progress(client, create_niche, create_profile):
    """Should reject new batch when niche already has active batch"""
    # Create niche and profiles
    niche = create_niche('Fitness')
    create_profile('user1', niche_id=niche.id)
    
    # Create first batch
    data = {'niche_id': niche.id, 'profile_count': 1}
    client.post('/api/batches', json=data)
    
    # Try to create second batch
    response = client.post('/api/batches', json=data)
    assert response.status_code == 400
    assert 'batch already in progress' in response.json['message'].lower()

def test_get_batch(client, create_niche, create_batch):
    """Should return specific batch by ID"""
    niche = create_niche('Fitness')
    batch = create_batch(niche.id)
    
    response = client.get(f'/api/batches/{batch.id}')
    assert response.status_code == 200
    assert response.json['id'] == batch.id
    assert response.json['niche_id'] == niche.id

def test_get_batch_not_found(client):
    """Should return 404 for non-existent batch"""
    response = client.get('/api/batches/nonexistent')
    assert response.status_code == 404

def test_cancel_batch(client, create_niche, create_batch):
    """Should cancel in-progress batch"""
    niche = create_niche('Fitness')
    batch = create_batch(niche.id)
    batch.start()  # Set to running
    
    response = client.post(f'/api/batches/{batch.id}/cancel')
    assert response.status_code == 200
    assert response.json['status'] == 'cancelled'

def test_cancel_completed_batch(client, create_niche, create_batch):
    """Should reject cancellation of completed batch"""
    niche = create_niche('Fitness')
    batch = create_batch(niche.id)
    batch.complete()  # Set to completed
    
    response = client.post(f'/api/batches/{batch.id}/cancel')
    assert response.status_code == 400
    assert 'cannot cancel' in response.json['message'].lower()

def test_get_batch_results(client, create_niche, create_profile, create_batch, create_story):
    """Should return story results for batch"""
    # Create test data
    niche = create_niche('Fitness')
    profile = create_profile('user1', niche_id=niche.id)
    batch = create_batch(niche.id)
    story = create_story(profile.id, batch.id)
    
    response = client.get(f'/api/batches/{batch.id}/results')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['profile_id'] == profile.id

def test_get_active_batches(client, create_niche, create_batch):
    """Should return only active (pending/running) batches"""
    niche = create_niche('Fitness')
    
    # Create batches in different states
    pending_batch = create_batch(niche.id)  # Status: pending
    
    running_batch = create_batch(niche.id)
    running_batch.start()  # Status: running
    
    completed_batch = create_batch(niche.id)
    completed_batch.complete()  # Status: completed
    
    response = client.get('/api/batches?status=active')
    assert response.status_code == 200
    assert len(response.json) == 2  # Only pending and running
    
    batch_statuses = [b['status'] for b in response.json]
    assert 'pending' in batch_statuses
    assert 'running' in batch_statuses
    assert 'completed' not in batch_statuses

def test_get_batch_progress(client, create_niche, create_profile, create_batch):
    """Should return batch progress details"""
    # Create test data
    niche = create_niche('Fitness')
    profiles = [create_profile(f'user{i}', niche_id=niche.id) for i in range(3)]
    batch = create_batch(niche.id)
    
    # Add profiles to batch
    for profile in profiles:
        BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
    
    # Mark some profiles as processed
    batch_profiles = BatchProfile.query.filter_by(batch_id=batch.id).all()
    batch_profiles[0].complete(has_story=True)
    batch_profiles[1].complete(has_story=False)
    # Leave one pending
    
    response = client.get(f'/api/batches/{batch.id}/progress')
    assert response.status_code == 200
    assert response.json['total_profiles'] == 3
    assert response.json['completed_profiles'] == 2
    assert response.json['successful_checks'] == 1
    assert response.json['pending_profiles'] == 1

def test_auto_trigger_batch(client, create_niche, create_profile):
    """Should auto-trigger batch when below story target"""
    # Create niche with target and profiles
    niche = create_niche('Fitness', daily_story_target=5)
    for i in range(10):
        create_profile(f'user{i}', niche_id=niche.id)
    
    response = client.post('/api/batches/auto-trigger')
    assert response.status_code == 200
    assert len(response.json['triggered']) == 1
    assert response.json['triggered'][0]['niche_id'] == niche.id

def test_cleanup_old_batches(client, create_niche, create_batch):
    """Should clean up old completed batches"""
    niche = create_niche('Fitness')
    
    # Create old completed batch
    old_batch = create_batch(niche.id)
    old_batch.complete()
    old_batch.end_time = datetime.utcnow() - timedelta(days=8)
    old_batch.save()
    
    # Create recent completed batch
    recent_batch = create_batch(niche.id)
    recent_batch.complete()
    
    response = client.post('/api/batches/cleanup')
    assert response.status_code == 200
    assert response.json['cleaned'] == 1
    
    # Verify old batch removed
    assert Batch.get_by_id(old_batch.id) is None
    # Verify recent batch remains
    assert Batch.get_by_id(recent_batch.id) is not None
