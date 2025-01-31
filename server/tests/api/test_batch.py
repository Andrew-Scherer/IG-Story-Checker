"""
Test Batch API
Tests for batch API endpoints with simplified state management
"""

import pytest
import json
from datetime import datetime, UTC
from models import db, Batch, Profile, Niche
from services.queue_manager import queue_manager

@pytest.fixture
def sample_niche(db_session):
    """Create a sample niche"""
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.commit()
    return niche

@pytest.fixture
def sample_profiles(db_session, sample_niche):
    """Create sample profiles"""
    profiles = []
    for i in range(2):
        profile = Profile(username=f'test_user_{i}', niche_id=sample_niche.id)
        db_session.add(profile)
        profiles.append(profile)
    db_session.commit()
    return profiles

@pytest.fixture
def sample_batch(db_session, sample_niche, sample_profiles):
    """Create a sample batch"""
    batch = Batch(niche_id=str(sample_niche.id), profile_ids=[p.id for p in sample_profiles])
    db_session.add(batch)
    db_session.commit()
    return batch

def test_create_batch(client, db_session, sample_niche, sample_profiles):
    """Test batch creation"""
    # Create batch
    response = client.post('/api/batches', json={
        'niche_id': str(sample_niche.id),
        'profile_ids': [str(p.id) for p in sample_profiles]
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    
    # Verify batch state
    batch = db_session.get(Batch, data['id'])
    assert batch is not None
    assert batch.status == 'queued'
    assert batch.queue_position == 0  # First batch gets position 0

def test_create_queued_batch(client, db_session, sample_niche, sample_profiles, sample_batch):
    """Test batch creation when another batch is running"""
    # Set up running batch
    sample_batch.status = 'in_progress'
    sample_batch.queue_position = 0
    db_session.commit()

    # Create new batch
    response = client.post('/api/batches', json={
        'niche_id': str(sample_niche.id),
        'profile_ids': [str(p.id) for p in sample_profiles]
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    
    # Verify batch is queued
    batch = db_session.get(Batch, data['id'])
    assert batch is not None
    assert batch.status == 'queued'
    assert batch.queue_position == 1  # Should be queued at position 1

def test_resume_batch(client, db_session, sample_batch):
    """Test batch resume"""
    # Set up paused batch
    sample_batch.status = 'paused'
    sample_batch.queue_position = None
    db_session.commit()

    # Resume batch
    response = client.post('/api/batches/resume', json={
        'batch_ids': [str(sample_batch.id)]
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify batch resumed
    db_session.refresh(sample_batch)
    assert sample_batch.status == 'in_progress'
    assert sample_batch.queue_position == 0

def test_resume_multiple_batches(client, db_session, sample_niche, sample_profiles):
    """Test resuming multiple batches"""
    # Create paused batches
    batches = []
    for i in range(2):
        batch = Batch(niche_id=str(sample_niche.id), profile_ids=[p.id for p in sample_profiles])
        batch.status = 'paused'
        db_session.add(batch)
        batches.append(batch)
    db_session.commit()

    # Resume batches
    response = client.post('/api/batches/resume', json={
        'batch_ids': [str(b.id) for b in batches]
    })
    assert response.status_code == 200
    
    # Verify batch states
    db_session.refresh(batches[0])
    db_session.refresh(batches[1])
    assert batches[0].status == 'in_progress'
    assert batches[0].queue_position == 0
    assert batches[1].status == 'in_progress'
    assert batches[1].queue_position == 1

def test_stop_batch(client, db_session, sample_batch):
    """Test batch stop"""
    # Set up running batch
    sample_batch.status = 'in_progress'
    sample_batch.queue_position = 0
    db_session.commit()

    # Stop batch
    response = client.post('/api/batches/stop', json={
        'batch_ids': [str(sample_batch.id)]
    })
    assert response.status_code == 200
    
    # Verify batch stopped
    db_session.refresh(sample_batch)
    assert sample_batch.status == 'paused'
    assert sample_batch.queue_position is None

def test_delete_batch(client, db_session, sample_batch):
    """Test batch deletion"""
    # Delete batch
    response = client.delete('/api/batches', json={
        'batch_ids': [str(sample_batch.id)]
    })
    assert response.status_code == 204
    
    # Verify batch deleted
    batch = db_session.get(Batch, sample_batch.id)
    assert batch is None

def test_get_batch_logs(client, db_session, sample_batch):
    """Test batch log retrieval"""
    # Create some logs
    for i in range(3):
        sample_batch.logs.append({
            'level': 'INFO',
            'message': f'Test log {i}',
            'timestamp': datetime.now(UTC)
        })
    db_session.commit()

    # Get logs
    response = client.get(f'/api/batches/{sample_batch.id}/logs')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify logs
    assert len(data['logs']) == 3
    assert data['total'] == 3
