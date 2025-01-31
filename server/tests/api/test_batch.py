"""
Test Batch API
Tests for batch operations endpoints
"""

import pytest
from server.extensions import db
from models import Batch, BatchLog

@pytest.mark.real_db
def test_batch_lifecycle(client, app, test_niche, test_profile):
    """Test complete batch lifecycle: create -> queue -> pause -> resume -> delete"""
    # Create batch
    response = client.post('/api/batches', json={
        'niche_id': test_niche.id,
        'profile_ids': [test_profile.id]
    })
    assert response.status_code == 201
    data = response.get_json()
    batch_id = data['id']
    
    # Verify queued state after creation
    batch = Batch.query.get(batch_id)
    assert batch.status == 'queued'
    assert isinstance(batch.position, int)
    
    # Pause batch
    response = client.post('/api/batches/stop', json={'batch_ids': [batch_id]})
    assert response.status_code == 200
    batch = Batch.query.get(batch_id)
    assert batch.status == 'paused'
    assert batch.position is None
    
    # Resume batch
    response = client.post('/api/batches/resume', json={'batch_ids': [batch_id]})
    assert response.status_code == 200
    batch = Batch.query.get(batch_id)
    assert batch.status == 'queued'
    assert isinstance(batch.position, int)
    
    # Delete batch
    response = client.delete('/api/batches', json={'batch_ids': [batch_id]})
    assert response.status_code == 204
    assert Batch.query.get(batch_id) is None

@pytest.mark.real_db
def test_batch_logs_created(client, app, test_batch):
    """Verify logs are created for batch state changes"""
    # Trigger a state change
    client.post('/api/batches/resume', json={'batch_ids': [test_batch.id]})
    
    # Check logs
    logs = BatchLog.query.filter_by(batch_id=test_batch.id).all()
    assert len(logs) > 0
    assert any('queued' in log.message.lower() for log in logs)

@pytest.mark.real_db
def test_batch_validation(client, app):
    """Test batch API input validation"""
    # Test missing niche_id
    response = client.post('/api/batches', json={})
    assert response.status_code == 400
    assert 'niche_id is required' in response.get_json()['error']
    
    # Test missing profile_ids
    response = client.post('/api/batches', json={'niche_id': 'test'})
    assert response.status_code == 400
    assert 'profile_ids is required' in response.get_json()['error']
    
    # Test missing batch_ids for operations
    response = client.post('/api/batches/stop', json={})
    assert response.status_code == 400
    assert 'batch_ids is required' in response.get_json()['error']

@pytest.mark.real_db
def test_batch_refresh(client, app, test_batch):
    """Test batch refresh functionality"""
    # First pause the batch
    client.post('/api/batches/stop', json={'batch_ids': [test_batch.id]})
    
    # Then refresh it
    response = client.post('/api/batches/refresh', json={'batch_ids': [test_batch.id]})
    assert response.status_code == 200
    
    # Verify it's back in queued state
    batch = Batch.query.get(test_batch.id)
    assert batch.status == 'queued'
    assert isinstance(batch.position, int)
