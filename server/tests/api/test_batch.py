"""
Tests for batch API endpoints focusing on core functionality
"""

import pytest
import json
from models import Batch, Profile, BatchProfile
from extensions import db

def test_create_batch_with_profiles(client, db_session, create_niche, create_profile):
    """Test creating a new batch with profiles"""
    # Create test niche and profiles
    niche = create_niche("Test Niche")
    profile1 = create_profile('test1', niche_id=str(niche.id))
    profile2 = create_profile('test2', niche_id=str(niche.id))

    # Create batch
    response = client.post('/api/batches', json={
        'niche_id': str(niche.id),
        'profile_ids': [profile1.id, profile2.id]
    })
    assert response.status_code == 201

    data = json.loads(response.data)
    assert data['niche_id'] == str(niche.id)
    assert data['status'] == 'queued'
    assert data['total_profiles'] == 2
    assert data['completed_profiles'] == 0
    assert data['successful_checks'] == 0
    assert data['failed_checks'] == 0

    # Verify batch profiles in database
    batch = db_session.get(Batch, data['id'])
    assert len(batch.profiles) == 2
    for batch_profile in batch.profiles:
        assert batch_profile.status == 'pending'
        assert batch_profile.proxy_id is None  # Proxy assigned during processing
        assert batch_profile.session_id is None  # Session assigned during processing

def test_create_batch_validation(client, db_session, create_niche, create_profile):
    """Test batch creation validation"""
    niche = create_niche("Test Niche")
    profile = create_profile('test1', niche_id=str(niche.id))

    # Missing niche_id
    response = client.post('/api/batches', json={
        'profile_ids': [profile.id]
    })
    assert response.status_code == 400

    # Missing profile_ids
    response = client.post('/api/batches', json={
        'niche_id': str(niche.id)
    })
    assert response.status_code == 400

    # Empty profile_ids
    response = client.post('/api/batches', json={
        'niche_id': str(niche.id),
        'profile_ids': []
    })
    assert response.status_code == 400

def test_start_batch_processing(client, db_session, create_niche, create_profile):
    """Test starting batch processing"""
    # Create test data
    niche = create_niche("Test Niche")
    profile1 = create_profile('test1', niche_id=str(niche.id))
    profile2 = create_profile('test2', niche_id=str(niche.id))

    # Create two queued batches
    queued_batch1 = Batch(niche_id=str(niche.id), profile_ids=[profile1.id])
    queued_batch2 = Batch(niche_id=str(niche.id), profile_ids=[profile2.id])
    db_session.add(queued_batch1)
    db_session.add(queued_batch2)
    db_session.commit()

    # Start first queued batch
    response = client.post('/api/batches/start', json={
        'batch_ids': [queued_batch1.id]
    })
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['id'] == queued_batch1.id
    assert data[0]['status'] == 'in_progress'

    # Verify first batch status in database
    queued_batch1 = db_session.get(Batch, queued_batch1.id)
    assert queued_batch1.status == 'in_progress'

    # Verify batch profiles are updated
    for batch_profile in queued_batch1.profiles:
        assert batch_profile.status == 'pending'

    # Try to start second batch (should fail)
    response = client.post('/api/batches/start', json={
        'batch_ids': [queued_batch2.id]
    })
    assert response.status_code == 409  # Conflict - another batch is running

    # Verify second batch status remains queued
    queued_batch2 = db_session.get(Batch, queued_batch2.id)
    assert queued_batch2.status == 'queued'

def test_complete_batch_workflow(client, db_session, create_niche, create_profile):
    """Test complete workflow from selection to processing"""
    # Create test data
    niche = create_niche("Test Niche")
    profiles = [create_profile(f'test{i}', niche_id=str(niche.id)) for i in range(5)]

    # Create multiple batches
    batches = [
        Batch(niche_id=str(niche.id), profile_ids=[profiles[0].id, profiles[1].id]),
        Batch(niche_id=str(niche.id), profile_ids=[profiles[2].id, profiles[3].id]),
        Batch(niche_id=str(niche.id), profile_ids=[profiles[4].id])
    ]
    db_session.add_all(batches)
    db_session.commit()

    # Start selected batches (first two)
    response = client.post('/api/batches/start', json={
        'batch_ids': [batches[0].id, batches[1].id]
    })
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 2
    assert {batch['id'] for batch in data} == {batches[0].id, batches[1].id}
    assert all(batch['status'] == 'in_progress' for batch in data)

    # Verify batch statuses in database
    for i, batch in enumerate(batches):
        batch = db_session.get(Batch, batch.id)
        if i < 2:
            assert batch.status == 'in_progress'
            for batch_profile in batch.profiles:
                assert batch_profile.status == 'pending'
        else:
            assert batch.status == 'queued'
            for batch_profile in batch.profiles:
                assert batch_profile.status == 'pending'

def test_stop_batch_processing(client, db_session, create_niche, create_profile):
    """Test stopping batch processing"""
    # Create test data
    niche = create_niche("Test Niche")
    profile = create_profile('test1', niche_id=str(niche.id))

    # Create and start batch
    batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
    batch.status = 'in_progress'
    db_session.add(batch)
    db_session.commit()

    # Stop batch
    response = client.post('/api/batches/stop', json={
        'batch_ids': [batch.id]
    })
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['id'] == batch.id
    assert data[0]['status'] == 'queued'

    # Verify batch status in database
    batch = db_session.get(Batch, batch.id)
    assert batch.status == 'queued'

def test_concurrent_batch_operations(client, db_session, create_niche, create_profile):
    """Test handling concurrent batch operations"""
    # Create test data
    niche = create_niche("Test Niche")
    profile1 = create_profile('test1', niche_id=str(niche.id))
    profile2 = create_profile('test2', niche_id=str(niche.id))

    # Create two batches
    batch1 = Batch(niche_id=str(niche.id), profile_ids=[profile1.id])
    batch2 = Batch(niche_id=str(niche.id), profile_ids=[profile2.id])
    db_session.add_all([batch1, batch2])
    db_session.commit()

    # Start first batch
    response = client.post('/api/batches/start', json={
        'batch_ids': [batch1.id]
    })
    assert response.status_code == 200

    # Try to start second batch while first is running
    response = client.post('/api/batches/start', json={
        'batch_ids': [batch2.id]
    })
    assert response.status_code == 409  # Conflict - another batch is running

    # Stop first batch
    response = client.post('/api/batches/stop', json={
        'batch_ids': [batch1.id]
    })
    assert response.status_code == 200

    # Now second batch should be able to start
    response = client.post('/api/batches/start', json={
        'batch_ids': [batch2.id]
    })
    assert response.status_code == 200

def test_list_batches_with_stats(client, db_session, create_niche, create_profile):
    """Test listing batches with stats"""
    # Create test data
    niche = create_niche("Test Niche")
    profile = create_profile('test1', niche_id=str(niche.id))

    # Create batch
    batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
    db_session.add(batch)
    db_session.commit()

    # Update batch stats
    batch.completed_profiles = 1
    batch.successful_checks = 1
    batch.failed_checks = 0
    batch.status = 'done'
    db_session.commit()

    # Get batches
    response = client.get('/api/batches')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['id'] == batch.id
    assert data[0]['niche_id'] == str(niche.id)
    assert data[0]['status'] == 'done'
    assert data[0]['total_profiles'] == 1
    assert data[0]['completed_profiles'] == 1
    assert data[0]['successful_checks'] == 1
    assert data[0]['failed_checks'] == 0
    assert data[0]['completion_rate'] == 100.0

def test_delete_batches(client, db_session, create_niche, create_profile):
    """Test deleting batches"""
    # Create test data
    niche = create_niche("Test Niche")
    profile = create_profile('test1', niche_id=str(niche.id))

    # Create batch
    batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
    db_session.add(batch)
    db_session.commit()

    # Verify batch and batch profiles exist
    assert db_session.query(Batch).count() == 1
    assert db_session.query(BatchProfile).count() == 1

    # Delete batch
    response = client.delete('/api/batches', json={
        'batch_ids': [batch.id]
    })
    assert response.status_code == 204

    # Verify batch and batch profiles are deleted
    assert db_session.query(Batch).count() == 0
    assert db_session.query(BatchProfile).count() == 0

def test_delete_nonexistent_batch(client, db_session):
    """Test deleting nonexistent batch"""
    response = client.delete('/api/batches', json={
        'batch_ids': ['nonexistent-id']
    })
    assert response.status_code == 404

def test_get_batch_logs(client, db_session, create_niche, create_profile):
    """Test retrieving batch logs"""
    # Create test data
    niche = create_niche("Test Niche")
    profile = create_profile('test1', niche_id=str(niche.id))
    
    # Create batch
    batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
    db_session.add(batch)
    db_session.commit()
    
    # Create some log entries
    from services.batch_log_service import BatchLogService
    BatchLogService.create_log(batch.id, 'BATCH_START', 'Batch started')
    BatchLogService.create_log(batch.id, 'PROFILE_CHECK_START', 'Checking profile', profile_id=profile.id)
    BatchLogService.create_log(batch.id, 'BATCH_END', 'Batch completed')
    
    # Retrieve logs
    response = client.get(f'/api/batches/{batch.id}/logs')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'logs' in data
    assert len(data['logs']) == 3
    assert data['total'] == 3
    
    # Check log entry structure
    log_entry = data['logs'][0]
    assert 'id' in log_entry
    assert 'batch_id' in log_entry
    assert 'timestamp' in log_entry
    assert 'event_type' in log_entry
    assert 'message' in log_entry
    
    # Test pagination
    response = client.get(f'/api/batches/{batch.id}/logs?limit=2&offset=1')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data['logs']) == 2
    assert data['total'] == 3
    assert data['limit'] == 2
    assert data['offset'] == 1
