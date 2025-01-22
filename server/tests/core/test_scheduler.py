"""
Test scheduler integration with batch processing
"""

import pytest
import asyncio
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch
from models import db, Batch, BatchProfile, Profile
from core.worker_manager import WorkerPool
from tasks import init_scheduler, shutdown_scheduler

@pytest.fixture
def mock_settings():
    """Mock system settings"""
    with patch('models.settings.SystemSettings') as mock:
        settings = Mock()
        settings.max_threads = 2
        settings.proxy_max_failures = 3
        settings.proxy_hourly_limit = 50
        mock.get_settings.return_value = settings
        yield settings

@pytest.fixture
def worker_pool(mock_settings):
    """Create worker pool for testing"""
    return WorkerPool()

@pytest.mark.asyncio
async def test_scheduler_batch_processing(app, worker_pool, create_niche, create_profile, create_proxy_session, db_session):
    """Test scheduler picks up and processes started batch"""
    with app.app_context():
        # Create test data
        niche = create_niche("Test Niche")
        profile = Profile(username='test_user', niche_id=str(niche.id))
        db_session.add(profile)
        db_session.commit()
        
        # Create batch
        batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
        db_session.add(batch)
        db_session.commit()
        
        # Create proxy-session pair
        proxy, session = create_proxy_session()
        worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)
        
        # Mock story checker
        with patch('core.worker_manager.StoryChecker') as mock_checker:
            checker = Mock()
            mock_checker.return_value = checker
            checker.check_profile = AsyncMock(return_value=True)
            
            # Initialize scheduler
            scheduler = init_scheduler()
            try:
                # Start batch via API
                response = app.test_client().post('/api/batches/start', json={
                    'batch_ids': [batch.id]
                })
                assert response.status_code == 200
                
                # Wait for scheduler to process batch (30 second interval)
                await asyncio.sleep(1)  # Should be picked up in first interval
                
                # Verify batch was processed
                db_session.refresh(batch)
                assert batch.status == 'done'
                assert batch.completed_profiles == 1
                assert batch.successful_checks == 1
                
                # Verify profile was processed
                batch_profile = BatchProfile.query.filter_by(batch_id=batch.id).first()
                assert batch_profile.status == 'done'
                assert batch_profile.has_story is True
                assert batch_profile.proxy_id == proxy.id
                
            finally:
                shutdown_scheduler(scheduler)

@pytest.mark.asyncio
async def test_scheduler_concurrent_batches(app, worker_pool, create_niche, create_profile, create_proxy_session, db_session):
    """Test scheduler handles concurrent batch starts correctly"""
    with app.app_context():
        # Create test data
        niche = create_niche("Test Niche")
        profiles = []
        for i in range(2):
            profile = Profile(username=f'user{i}', niche_id=str(niche.id))
            db_session.add(profile)
            db_session.commit()
            profiles.append(profile)
        
        # Create two batches
        batch1 = Batch(niche_id=str(niche.id), profile_ids=[profiles[0].id])
        batch2 = Batch(niche_id=str(niche.id), profile_ids=[profiles[1].id])
        db_session.add_all([batch1, batch2])
        db_session.commit()
        
        # Create proxy
        proxy, session = create_proxy_session()
        worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)
        
        # Mock story checker
        with patch('core.worker_manager.StoryChecker') as mock_checker:
            checker = Mock()
            mock_checker.return_value = checker
            checker.check_profile = AsyncMock(return_value=True)
            
            # Initialize scheduler
            scheduler = init_scheduler()
            try:
                # Try to start both batches simultaneously
                client = app.test_client()
                response1 = client.post('/api/batches/start', json={
                    'batch_ids': [batch1.id]
                })
                response2 = client.post('/api/batches/start', json={
                    'batch_ids': [batch2.id]
                })
                
                # First batch should start
                assert response1.status_code == 200
                # Second batch should be rejected
                assert response2.status_code == 409
                
                # Wait for scheduler to process first batch
                await asyncio.sleep(1)
                
                # Verify first batch completed
                db_session.refresh(batch1)
                assert batch1.status == 'done'
                assert batch1.completed_profiles == 1
                
                # Verify second batch still queued
                db_session.refresh(batch2)
                assert batch2.status == 'queued'
                
            finally:
                shutdown_scheduler(scheduler)

@pytest.mark.asyncio
async def test_scheduler_batch_failure_recovery(app, worker_pool, create_niche, create_profile, create_proxy_session, db_session):
    """Test scheduler handles batch processing failures"""
    with app.app_context():
        # Create test data
        niche = create_niche("Test Niche")
        profile = Profile(username='test_user', niche_id=str(niche.id))
        db_session.add(profile)
        db_session.commit()
        
        # Create batch
        batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
        db_session.add(batch)
        db_session.commit()
        
        # Create proxy
        proxy, session = create_proxy_session()
        worker_pool.add_proxy_session(f"http://{proxy.ip}:{proxy.port}", session.session)
        
        # Mock story checker to fail first try, succeed second try
        with patch('core.worker_manager.StoryChecker') as mock_checker:
            checker = Mock()
            mock_checker.return_value = checker
            checker.check_profile = AsyncMock(side_effect=[
                Exception("Connection error"),
                True
            ])
            
            # Initialize scheduler
            scheduler = init_scheduler()
            try:
                # Start batch
                response = app.test_client().post('/api/batches/start', json={
                    'batch_ids': [batch.id]
                })
                assert response.status_code == 200
                
                # Wait for first attempt
                await asyncio.sleep(1)
                
                # Verify batch failed and was requeued
                db_session.refresh(batch)
                assert batch.status == 'queued'
                
                # Wait for second attempt
                await asyncio.sleep(1)
                
                # Verify batch completed on retry
                db_session.refresh(batch)
                assert batch.status == 'done'
                assert batch.completed_profiles == 1
                assert batch.successful_checks == 1
                
            finally:
                shutdown_scheduler(scheduler)
