"""
Test Queue Manager
Tests batch queue management and processing order
"""

import pytest
from datetime import datetime, UTC
from models.batch import Batch
from models.niche import Niche
from core.queue_manager import QueueManager

@pytest.fixture
def queue_manager():
    """Create queue manager for testing"""
    return QueueManager(max_concurrent_batches=2)

@pytest.fixture
def niche(db_session):
    """Create test niche"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()
    return niche

@pytest.fixture
def batch(db_session, niche):
    """Create test batch"""
    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()
    return batch

def test_add_batch(queue_manager, batch, db_session):
    """Test adding batch to queue"""
    queue_manager.add_batch(batch, db_session)
    
    # Check batch is in queue without starting it
    next_batch = queue_manager.peek_next_batch(db_session)
    assert next_batch.id == batch.id
    assert next_batch.status == 'pending'
    
    # Now get and start the batch
    active_batch = queue_manager.get_next_batch(db_session)
    assert active_batch.id == batch.id
    assert active_batch.status == 'running'

def test_get_next_batch_fifo(queue_manager, db_session, niche):
    """Test batches are processed in FIFO order"""
    # Create multiple batches
    batch1 = Batch(niche_id=niche.id)
    batch2 = Batch(niche_id=niche.id)
    db_session.add_all([batch1, batch2])
    db_session.commit()
    
    # Add to queue in order
    queue_manager.add_batch(batch1, db_session)
    queue_manager.add_batch(batch2, db_session)
    
    # Should get first batch added
    next_batch = queue_manager.get_next_batch(db_session)
    assert next_batch.id == batch1.id
    
    # Then second batch
    next_batch = queue_manager.get_next_batch(db_session)
    assert next_batch.id == batch2.id
    
    # No more batches
    assert queue_manager.get_next_batch(db_session) is None

def test_remove_batch(queue_manager, batch, db_session):
    """Test removing batch from queue"""
    queue_manager.add_batch(batch, db_session)
    queue_manager.remove_batch(batch.id)
    
    assert queue_manager.get_next_batch(db_session) is None

def test_concurrent_batch_limit(queue_manager, db_session, niche):
    """Test maximum concurrent batch limit"""
    # Create max_concurrent_batches + 1 batches
    batches = [
        Batch(niche_id=niche.id)
        for _ in range(queue_manager.max_concurrent_batches + 1)
    ]
    db_session.add_all(batches)
    db_session.commit()
    
    # Add all batches to queue
    for batch in batches:
        queue_manager.add_batch(batch, db_session)
    
    # Should only get max_concurrent_batches number of batches
    active_batches = []
    while True:
        batch = queue_manager.get_next_batch(db_session)
        if batch is None:
            break
        active_batches.append(batch)
    
    assert len(active_batches) == queue_manager.max_concurrent_batches

def test_batch_state_transitions(queue_manager, batch, db_session):
    """Test batch state changes when processed"""
    queue_manager.add_batch(batch, db_session)
    
    # Getting next batch should mark it as running
    active_batch = queue_manager.get_next_batch(db_session)
    db_session.refresh(batch)
    
    assert active_batch.id == batch.id
    assert batch.status == 'running'
    assert batch.start_time is not None

def test_completed_batch_removal(queue_manager, batch, db_session):
    """Test completed batches are removed from queue"""
    queue_manager.add_batch(batch, db_session)
    
    # Complete the batch
    batch.complete()
    db_session.commit()
    
    # Should not get completed batch
    assert queue_manager.get_next_batch(db_session) is None

def test_failed_batch_handling(queue_manager, batch, db_session):
    """Test failed batches are removed from queue"""
    queue_manager.add_batch(batch, db_session)
    
    # Fail the batch
    batch.fail("Test error")
    db_session.commit()
    
    # Should not get failed batch
    assert queue_manager.get_next_batch(db_session) is None

def test_get_active_batches(queue_manager, db_session, niche):
    """Test getting currently active batches"""
    # Create and start some batches
    batch1 = Batch(niche_id=niche.id)
    batch2 = Batch(niche_id=niche.id)
    db_session.add_all([batch1, batch2])
    db_session.commit()
    
    queue_manager.add_batch(batch1, db_session)
    queue_manager.add_batch(batch2, db_session)
    
    # Get batches to make them active
    batch1 = queue_manager.get_next_batch(db_session)
    batch2 = queue_manager.get_next_batch(db_session)
    
    active_batches = queue_manager.get_active_batches(db_session)
    assert len(active_batches) == 2
    assert {b.id for b in active_batches} == {batch1.id, batch2.id}

def test_clear_queue(queue_manager, db_session, niche):
    """Test clearing all batches from queue"""
    # Add multiple batches
    batches = [
        Batch(niche_id=niche.id)
        for _ in range(3)
    ]
    db_session.add_all(batches)
    db_session.commit()
    
    for batch in batches:
        queue_manager.add_batch(batch, db_session)
    
    # Clear queue
    queue_manager.clear()
    
    # Queue should be empty
    assert queue_manager.get_next_batch(db_session) is None
    assert len(queue_manager.get_active_batches(db_session)) == 0
