"""
Test Batch Manager
Tests for simplified batch queue management
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, UTC
from services.batch_manager import BatchManager
from models.batch import Batch

def setup_mock_db(db_session, batches=None):
    """Setup mock database session with proper query chain returns
    
    Args:
        db_session: Mock db session
        batches: Optional list of mock batches to use in query results
    """
    mock_query = Mock()
    db_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    # Configure default returns
    mock_query.scalar.return_value = 0  # For _get_next_position
    mock_query.all.return_value = batches or []  # For reorder_queue
    mock_query.first.return_value = None  # For _get_running_batch
    
    return mock_query

def test_basic_queue_operations():
    """Test basic queue operations without database"""
    # Create mock objects
    batch = Mock(spec=Batch, id='123', status='queued', position=None)
    
    db_session = MagicMock()
    db_session.get.return_value = batch
    mock_query = setup_mock_db(db_session)
    
    # Create manager with mock session
    manager = BatchManager(db_session)
    
    # Test queue operations
    manager.queue_batch(batch.id)
    assert batch.status == 'queued'
    assert batch.position == 1  # Next position is 1 since scalar returns 0
    
    # Mock no running batch for start_batch
    mock_query.first.return_value = None
    
    manager.start_batch(batch.id)
    assert batch.status == 'running'
    assert batch.position == 0
    
    manager.pause_batch(batch.id)
    assert batch.status == 'paused'
    assert batch.position is None

def test_batch_not_found():
    """Test handling of non-existent batch"""
    db_session = MagicMock()
    db_session.get.return_value = None
    setup_mock_db(db_session)
    
    manager = BatchManager(db_session)
    
    assert not manager.queue_batch('123')
    assert not manager.start_batch('123')
    assert not manager.pause_batch('123')

def test_queue_ordering():
    """Test queue position management"""
    # Create mock batches
    batch1 = Mock(spec=Batch, id='1', status='queued', position=None)
    batch2 = Mock(spec=Batch, id='2', status='queued', position=None)
    
    # Create mock session that returns different batches based on id
    db_session = MagicMock()
    def get_batch(model, batch_id):
        return {'1': batch1, '2': batch2}.get(batch_id)
    db_session.get.side_effect = get_batch
    
    # Setup mock query with sequential positions
    mock_query = setup_mock_db(db_session)
    mock_query.scalar.side_effect = [0, 1]  # First call returns 0, second returns 1
    
    manager = BatchManager(db_session)
    
    # Queue batches
    manager.queue_batch(batch1.id)
    assert batch1.position == 1
    
    manager.queue_batch(batch2.id)
    assert batch2.position == 2
    
    # Mock no running batch for start_batch
    mock_query.first.return_value = None
    
    # Start first batch
    manager.start_batch(batch1.id)
    assert batch1.position == 0
    assert batch1.status == 'running'
    assert batch2.position == 2  # Second batch position unchanged

def test_completion_timestamp():
    """Test completion timestamp setting"""
    batch = Mock(spec=Batch)
    batch.id = '123'
    batch.status = 'running'
    batch.position = 0
    batch.completed_at = None
    
    db_session = MagicMock()
    db_session.get.return_value = batch
    setup_mock_db(db_session)
    
    manager = BatchManager(db_session)
    
    # Mark batch as done
    manager.complete_batch(batch.id)
    
    assert batch.status == 'done'
    assert batch.position is None
    assert batch.completed_at is not None
    assert isinstance(batch.completed_at, datetime)
    assert batch.completed_at.tzinfo == UTC

def test_batch_promotion():
    """Test batch promotion logic"""
    # Create mock batches
    batch1 = Mock(spec=Batch, id='1', status='queued', position=1)
    batch2 = Mock(spec=Batch, id='2', status='queued', position=2)
    
    # Mock session with query capabilities
    db_session = MagicMock()
    db_session.get.side_effect = lambda model, batch_id: {'1': batch1, '2': batch2}.get(batch_id)
    
    # Setup mock query to return no running batch, then batch1 as next in queue
    mock_query = setup_mock_db(db_session, [batch1, batch2])
    mock_query.first.side_effect = [None, batch1]  # First call for running batch, second for next batch
    
    manager = BatchManager(db_session)
    
    # Promote next batch
    promoted = manager.promote_next_batch()
    
    # Debug prints
    print(f"DEBUG: batch1.position = {batch1.position}")
    print(f"DEBUG: promoted.position = {promoted.position}")
    
    assert promoted == batch1
    assert batch1.status == 'running'
    assert batch1.position == 0
    assert batch2.position == 1  # Should move up in queue

def test_error_handling():
    """Test batch error handling"""
    batch = Mock(spec=Batch)
    batch.id = '123'
    batch.status = 'running'
    batch.position = 0
    batch.error = None
    
    db_session = MagicMock()
    db_session.get.return_value = batch
    setup_mock_db(db_session)
    
    manager = BatchManager(db_session)
    
    # Handle error
    error_msg = "Test error"
    manager.handle_error(batch.id, error_msg)
    
    assert batch.status == 'error'
    assert batch.position is None
    assert batch.error == error_msg

def test_queue_reordering():
    """Test queue reordering after position changes"""
    # Create mock batches
    batches = [
        Mock(spec=Batch, id='1', status='queued', position=1),
        Mock(spec=Batch, id='2', status='queued', position=3),  # Gap in positions
        Mock(spec=Batch, id='3', status='queued', position=4)
    ]
    
    # Mock session with query capabilities
    db_session = MagicMock()
    setup_mock_db(db_session, batches)
    
    manager = BatchManager(db_session)
    
    # Reorder queue
    manager.reorder_queue()
    
    # Verify positions are sequential
    assert batches[0].position == 1
    assert batches[1].position == 2  # Fixed gap
    assert batches[2].position == 3

def test_batch_status_updates():
    """Test batch status and progress updates"""
    batch = Mock(spec=Batch)
    batch.id = '123'
    batch.status = 'running'
    batch.position = 0
    batch.total_profiles = 10
    batch.completed_profiles = 0
    batch.successful_checks = 0
    batch.failed_checks = 0
    
    db_session = MagicMock()
    db_session.get.return_value = batch
    setup_mock_db(db_session)
    
    manager = BatchManager(db_session)
    
    # Update progress
    manager.update_progress(batch.id, completed=5, successful=3, failed=2)
    
    assert batch.completed_profiles == 5
    assert batch.successful_checks == 3
    assert batch.failed_checks == 2
    
    # Complete all profiles
    manager.update_progress(batch.id, completed=10, successful=7, failed=3)
    
    assert batch.status == 'done'
    assert batch.position is None
    assert batch.completed_at is not None

def test_concurrent_batch_operations():
    """Test handling of concurrent batch operations"""
    batch1 = Mock(spec=Batch, id='1', status='queued', position=1)
    batch2 = Mock(spec=Batch, id='2', status='queued', position=2)
    
    db_session = MagicMock()
    db_session.get.side_effect = lambda model, batch_id: {'1': batch1, '2': batch2}.get(batch_id)
    
    # Setup mock query to handle running batch checks
    mock_query = setup_mock_db(db_session)
    mock_query.first.side_effect = [None, batch1]  # First None allows start, then returns batch1 as running
    
    manager = BatchManager(db_session)
    
    # Start first batch
    assert manager.start_batch(batch1.id)
    assert batch1.status == 'running'
    assert batch1.position == 0
    
    # Try to start second batch while first is running
    assert not manager.start_batch(batch2.id)
    assert batch2.status == 'queued'
    assert batch2.position == 2

def test_resume_paused_batch():
    """Test resuming a paused batch"""
    # Create mock batch
    batch = Mock(spec=Batch, id='1', status='paused', position=None)
    
    # Mock session with query capabilities
    db_session = MagicMock()
    db_session.get.return_value = batch
    
    # Setup mock query to return no running batch
    mock_query = setup_mock_db(db_session)
    mock_query.scalar.return_value = 0  # Next position will be 1
    mock_query.first.side_effect = [None, batch]  # No running batch, then batch as next in queue
    
    manager = BatchManager(db_session)
    
    # Queue the paused batch (resume)
    success = manager.queue_batch(batch.id)
    assert success, "Failed to queue paused batch"
    assert batch.status == 'queued'
    assert batch.position == 1, "Resumed batch should get position 1"
    
    # Since no batch is running, it should get promoted
    promoted = manager.promote_next_batch()
    assert promoted == batch, "Paused batch should be promoted"
    assert batch.status == 'running'
    assert batch.position == 0, "Promoted batch should get position 0"

def test_resume_paused_batch_with_promotion():
    """Test resuming a paused batch and promoting it to running"""
    # Create mock batch
    batch = Mock(spec=Batch, id='1', status='paused', position=None)
    
    # Mock session with query capabilities
    db_session = MagicMock()
    db_session.get.return_value = batch
    
    # Setup mock query to return no running batch
    mock_query = setup_mock_db(db_session)
    mock_query.scalar.return_value = 0  # Next position will be 1
    mock_query.first.side_effect = [None, batch]  # No running batch, then batch as next in queue
    
    manager = BatchManager(db_session)
    
    # Queue the paused batch (resume)
    success = manager.queue_batch(batch.id)
    assert success, "Failed to queue paused batch"
    assert batch.status == 'queued', "Batch should be queued first"
    assert batch.position == 1, "Queued batch should get next position"
    
    # Since no batch is running, we can promote it
    promoted = manager.promote_next_batch()
    assert promoted == batch, "Batch should be promoted"
    assert batch.status == 'running', "Promoted batch should be running"
    assert batch.position == 0, "Running batch should get position 0"
    
    # Verify commit was called for both operations
    assert db_session.commit.call_count == 2

def test_batch_state_validation():
    """Test batch state validation"""
    batch = Mock(spec=Batch, id='1', status='done', position=None)
    
    db_session = MagicMock()
    db_session.get.return_value = batch
    mock_query = setup_mock_db(db_session)
    mock_query.scalar.return_value = 0  # Next position will be 1
    
    manager = BatchManager(db_session)
    
    # Cannot start a completed batch without reset
    assert not manager.start_batch(batch.id)
    assert batch.status == 'done'
    
    # Reset and queue should work
    manager.reset_batch(batch.id)
    assert batch.status == 'queued'
    assert batch.position == 1
    assert batch.completed_at is None