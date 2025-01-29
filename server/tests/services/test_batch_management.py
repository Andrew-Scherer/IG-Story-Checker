"""
Tests for batch management implementation
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
from models import db, Batch, BatchProfile, Niche, Profile
from models.batch_log import BatchLog
from services.batch_state_manager import BatchStateManager
from services.batch_execution_manager import BatchExecutionManager
from services.queue_manager import QueueManager

@pytest.fixture(autouse=True)
def cleanup_database(app):
    """Clean up database before each test"""
    with app.app_context():
        # Delete all data from tables in reverse order of dependencies
        db.session.query(BatchLog).delete()  # Delete logs first
        db.session.query(BatchProfile).delete()
        db.session.query(Batch).delete()
        db.session.query(Profile).delete()
        db.session.query(Niche).delete()
        db.session.commit()

@pytest.fixture
def state_manager(app):
    """Create BatchStateManager instance"""
    with app.app_context():
        return BatchStateManager()

@pytest.fixture
def execution_manager(app, state_manager):
    """Create BatchExecutionManager instance"""
    with app.app_context():
        return BatchExecutionManager(state_manager)

@pytest.fixture
def queue_manager(app):
    """Create QueueManager instance"""
    with app.app_context():
        return QueueManager()

@pytest.fixture
def test_niche(app, request):
    """Create a test niche with unique name"""
    with app.app_context():
        # Use a shorter unique name
        niche_name = f"Niche-{request.node.name[:20]}"
        niche = Niche(name=niche_name)
        db.session.add(niche)
        db.session.commit()
        # Refresh the session to avoid detached instance errors
        db.session.refresh(niche)
        return niche

@pytest.fixture
def test_profiles(app, test_niche):
    """Create test profiles"""
    with app.app_context():
        profiles = []
        for i in range(2):
            profile = Profile(
                username=f"test_user_{i}",
                niche_id=test_niche.id
            )
            db.session.add(profile)
            profiles.append(profile)
        db.session.commit()
        # Refresh the session to avoid detached instance errors
        for profile in profiles:
            db.session.refresh(profile)
        return profiles

@pytest.fixture
def sample_batch(app, test_niche, test_profiles):
    """Create a sample batch for testing"""
    with app.app_context():
        profile_ids = [p.id for p in test_profiles]
        batch = Batch(
            niche_id=test_niche.id,
            profile_ids=profile_ids
        )
        batch.queue_position = 1
        db.session.add(batch)
        db.session.commit()
        # Refresh the session to avoid detached instance errors
        db.session.refresh(batch)
        return batch

def test_state_manager_mark_completed(app, state_manager, sample_batch):
    """Test marking a batch as completed"""
    with app.app_context():
        # Mark batch as completed
        state_manager.mark_completed(sample_batch.id)
        
        # Verify batch state
        batch = db.session.get(Batch, sample_batch.id)
        assert batch.status == 'done'
        assert batch.queue_position is None

def test_state_manager_move_to_end(app, state_manager, sample_batch):
    """Test moving a batch to the end of queue"""
    with app.app_context():
        # Move batch to end
        state_manager.move_to_end(sample_batch)
        
        # Verify batch state
        batch = db.session.get(Batch, sample_batch.id)
        assert batch.status == 'queued'
        assert batch.queue_position > 1
        assert batch.completed_profiles == 0
        assert batch.successful_checks == 0
        assert batch.failed_checks == 0

def test_execution_manager_handle_completion(app, execution_manager, state_manager, sample_batch):
    """Test handling batch completion"""
    with app.app_context():
        # Mock worker pool
        mock_worker_pool = Mock()
        app.worker_pool = mock_worker_pool
        
        # Handle completion
        execution_manager.handle_completion(sample_batch.id)
        
        # Verify batch state
        batch = db.session.get(Batch, sample_batch.id)
        assert batch.status == 'done'
        assert batch.queue_position is None
        
        # Verify worker pool interaction
        mock_worker_pool.unregister_batch.assert_called_once_with(sample_batch.id)

def test_execution_manager_handle_failure(app, execution_manager, state_manager, sample_batch):
    """Test handling batch failure"""
    with app.app_context():
        # Mock worker pool
        mock_worker_pool = Mock()
        app.worker_pool = mock_worker_pool
        
        # Handle failure
        error_msg = "Test error"
        execution_manager.handle_failure(sample_batch.id, error_msg)
        
        # Verify batch state
        batch = db.session.get(Batch, sample_batch.id)
        assert batch.status == 'queued'
        assert batch.queue_position > 1
        assert batch.completed_profiles == 0
        
        # Verify worker pool interaction
        mock_worker_pool.unregister_batch.assert_called_once_with(sample_batch.id)

def test_queue_manager_promote_next_batch(app, queue_manager, sample_batch):
    """Test promoting next batch in queue"""
    with app.app_context():
        # Mock worker pool
        mock_worker_pool = Mock()
        app.worker_pool = mock_worker_pool
        
        # Promote next batch
        promoted_batch = queue_manager.promote_next_batch()
        
        # Verify batch state
        assert promoted_batch.id == sample_batch.id
        assert promoted_batch.queue_position == 0
        
        # Verify worker pool interactions
        mock_worker_pool.register_batch.assert_called_once_with(sample_batch.id)
        assert mock_worker_pool.submit.called

def test_queue_manager_mark_completed_promotes_next(app, queue_manager, sample_batch, test_niche, test_profiles):
    """Test marking batch completed promotes next batch"""
    with app.app_context():
        # Create another batch in queue
        next_batch = Batch(
            niche_id=test_niche.id,
            profile_ids=[test_profiles[0].id]
        )
        next_batch.queue_position = 2
        db.session.add(next_batch)
        db.session.commit()
        
        # Mock worker pool
        mock_worker_pool = Mock()
        app.worker_pool = mock_worker_pool
        
        # Mark current batch completed
        queue_manager.mark_completed(sample_batch.id)
        
        # Verify first batch state
        batch = db.session.get(Batch, sample_batch.id)
        assert batch.status == 'done'
        assert batch.queue_position is None
        
        # Verify next batch was promoted
        next_batch = db.session.get(Batch, next_batch.id)
        assert next_batch.queue_position == 0

def test_no_circular_imports():
    """Test that circular imports have been eliminated"""
    # This will raise an ImportError if circular imports exist
    from services.queue_manager import QueueManager
    from services.batch_state_manager import BatchStateManager
    from services.batch_execution_manager import BatchExecutionManager
    
    # Verify we can create instances without circular import errors
    state_manager = BatchStateManager()
    execution_manager = BatchExecutionManager(state_manager)
    queue_manager = QueueManager()