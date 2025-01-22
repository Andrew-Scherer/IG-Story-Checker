"""
Integration tests for complete batch workflow with just-in-time proxy assignment
"""

import pytest
pytestmark = pytest.mark.asyncio
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch
from models import db, Profile, Batch, BatchProfile
from core.worker_manager import WorkerPool
from core.batch_processor import process_batch

@pytest.fixture
async def cleanup_sessions():
    """Clean up any unclosed client sessions"""
    yield
    # Import here to avoid circular imports
    from core.story_checker import SimpleStoryChecker
    for session in SimpleStoryChecker._sessions.values():
        if not session.closed:
            await session.close()
    SimpleStoryChecker._sessions.clear()

@pytest.mark.asyncio
async def test_complete_batch_workflow(client, db_session, create_niche, create_profile, create_proxy_session, cleanup_sessions):
    """Test complete workflow from profile selection to batch completion"""
    # 1. Setup
    # Create test niche and profiles
    niche = create_niche("Test Niche")
    profile1 = create_profile('test1', niche_id=str(niche.id))
    profile2 = create_profile('test2', niche_id=str(niche.id))
    
    # Create proxy-session pairs (but don't assign them yet)
    proxy1, session1 = create_proxy_session('http://proxy1:8080')
    proxy2, session2 = create_proxy_session('http://proxy2:8080')
    
    # 2. Create batch (without proxy assignment)
    response = client.post('/api/batches', json={
        'niche_id': str(niche.id),
        'profile_ids': [profile1.id, profile2.id]
    })
    assert response.status_code == 201
    batch_data = response.get_json()
    
    # Verify batch appears in list
    response = client.get('/api/batches')
    assert response.status_code == 200
    batches = response.get_json()
    assert len(batches) == 1
    assert batches[0]['id'] == batch_data['id']
    
    # Mock story checker
    with patch('core.story_checker.SimpleStoryChecker.initialize') as mock_init, \
         patch('core.story_checker.SimpleStoryChecker.check_story') as mock_check_story:
        # Configure mocks
        mock_init.return_value = None
        mock_check_story.side_effect = [True, False]  # First profile has story, second doesn't
        
        # 3. Start batch processing
        response = client.post('/api/batches/start', json={
            'batch_ids': [batch_data['id']]
        })
        assert response.status_code == 200
        
        # Create worker pool and add proxies
        worker_pool = WorkerPool()
        worker_pool.add_proxy_session(f"http://{proxy1.ip}:{proxy1.port}", session1.session)
        worker_pool.add_proxy_session(f"http://{proxy2.ip}:{proxy2.port}", session2.session)
        
        # Process batch
        await process_batch(batch_data['id'], worker_pool)
        
        # 4. Verify results
        # Check batch updates
        batch = db.session.get(Batch, batch_data['id'])
        assert batch.status == 'done'
        assert batch.completed_profiles == 2
        assert batch.successful_checks == 1
        assert batch.failed_checks == 1
        assert batch.completion_rate == 100.0
        
        # Check batch profile updates
        batch_profiles = BatchProfile.query.filter_by(batch_id=batch.id).all()
        assert len(batch_profiles) == 2
        
        # First profile should have story
        bp1 = next(bp for bp in batch_profiles if bp.profile_id == profile1.id)
        assert bp1.status == 'completed'
        assert bp1.has_story is True
        assert bp1.processed_at is not None
        assert bp1.error is None
        
        # Second profile should not have story
        bp2 = next(bp for bp in batch_profiles if bp.profile_id == profile2.id)
        assert bp2.status == 'completed'
        assert bp2.has_story is False
        assert bp2.processed_at is not None
        assert bp2.error is None
        
        # Check profile updates
        profile1 = db.session.get(Profile, profile1.id)
        assert profile1.active_story is True
        assert profile1.last_story_detected is not None
        assert profile1.total_checks == 1
        assert profile1.total_detections == 1
        
        profile2 = db.session.get(Profile, profile2.id)
        assert profile2.active_story is False
        assert profile2.last_story_detected is None
        assert profile2.total_checks == 1
        assert profile2.total_detections == 0

@pytest.mark.asyncio
async def test_concurrent_batch_processing(client, db_session, create_niche, create_profile, create_proxy_session, cleanup_sessions):
    """Test handling of concurrent batch processing"""
    # Setup test data
    niche = create_niche("Test Niche")
    profile1 = create_profile('test1', niche_id=str(niche.id))
    profile2 = create_profile('test2', niche_id=str(niche.id))
    proxy1, session1 = create_proxy_session('http://proxy1:8080')
    proxy2, session2 = create_proxy_session('http://proxy2:8080')
    
    # Create first batch
    response = client.post('/api/batches', json={
        'niche_id': str(niche.id),
        'profile_ids': [profile1.id]
    })
    batch1_data = response.get_json()
    
    # Create second batch
    response = client.post('/api/batches', json={
        'niche_id': str(niche.id),
        'profile_ids': [profile2.id]
    })
    batch2_data = response.get_json()
    
    # Mock story checker
    with patch('core.story_checker.SimpleStoryChecker.initialize') as mock_init, \
         patch('core.story_checker.SimpleStoryChecker.check_story') as mock_check_story:
        # Configure mocks
        mock_init.return_value = None
        mock_check_story.side_effect = [
            True,  # First batch succeeds
            Exception("Rate limited"),  # Second batch first try fails
            True  # Second batch second try succeeds
        ]
        
        # Start first batch
        response = client.post('/api/batches/start', json={
            'batch_ids': [batch1_data['id']]
        })
        assert response.status_code == 200
        
        # Try to start second batch while first is running
        response = client.post('/api/batches/start', json={
            'batch_ids': [batch2_data['id']]
        })
        assert response.status_code == 409  # Conflict - another batch is running
        
        # Setup worker pool
        worker_pool = WorkerPool()
        worker_pool.add_proxy_session(f"http://{proxy1.ip}:{proxy1.port}", session1.session)
        worker_pool.add_proxy_session(f"http://{proxy2.ip}:{proxy2.port}", session2.session)
        
        # Process first batch
        await process_batch(batch1_data['id'], worker_pool)
        
        # Verify first batch completed
        batch1 = db.session.get(Batch, batch1_data['id'])
        assert batch1.status == 'done'
        assert batch1.completed_profiles == 1
        assert batch1.successful_checks == 1
        assert batch1.failed_checks == 0
        
        # Verify first batch profile
        bp1 = BatchProfile.query.filter_by(batch_id=batch1.id).first()
        assert bp1.status == 'completed'
        assert bp1.has_story is True
        assert bp1.processed_at is not None
        assert bp1.error is None
        
        # Verify second batch still queued
        batch2 = db.session.get(Batch, batch2_data['id'])
        assert batch2.status == 'queued'
        
        # Now start and process second batch
        response = client.post('/api/batches/start', json={
            'batch_ids': [batch2_data['id']]
        })
        assert response.status_code == 200
        
        await process_batch(batch2_data['id'], worker_pool)
        
        # Verify second batch completed
        batch2 = db.session.get(Batch, batch2_data['id'])
        assert batch2.status == 'done'
        assert batch2.completed_profiles == 1
        assert batch2.successful_checks == 1
        assert batch2.failed_checks == 0
        
        # Verify second batch profile
        bp2 = BatchProfile.query.filter_by(batch_id=batch2.id).first()
        assert bp2.status == 'completed'
        assert bp2.has_story is True
        assert bp2.processed_at is not None
        assert bp2.error is None  # Error should be cleared after successful retry
