"""
Test Batch Management
Tests for batch state transitions and queue management
"""

import pytest
from datetime import datetime, UTC
from models import db, Batch, BatchProfile, Profile, Niche
from services.batch_state_manager import BatchStateManager
from services.queue_manager import QueueManager

@pytest.fixture
def state_manager(db_session):
    """Create BatchStateManager instance"""
    return BatchStateManager()

@pytest.fixture
def queue_manager(db_session, state_manager):
    """Create QueueManager instance"""
    manager = QueueManager()
    manager.state_manager = state_manager
    return manager

@pytest.fixture
def sample_batch(db_session):
    """Create a sample batch for testing"""
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.flush()

    profiles = []
    for i in range(2):
        profile = Profile(username=f'test_user_{i}', niche_id=niche.id)
        db_session.add(profile)
        profiles.append(profile)
    db_session.flush()

    batch = Batch(niche_id=str(niche.id), profile_ids=[p.id for p in profiles])
    db_session.add(batch)
    db_session.flush()
    return batch

def test_state_transitions(db_session, state_manager, queue_manager, sample_batch, worker_pool):
    """Test batch state transitions"""
    # Initial state
    assert sample_batch.status == 'queued'
    assert sample_batch.queue_position is None

    # Transition to in_progress
    assert state_manager.transition_state(sample_batch, 'in_progress', 0)
    db_session.refresh(sample_batch)
    assert sample_batch.status == 'in_progress'
    assert sample_batch.queue_position == 0
    worker_pool.register_batch.assert_called_once_with(sample_batch.id)

    # Transition to paused
    assert state_manager.transition_state(sample_batch, 'paused', None)
    db_session.refresh(sample_batch)
    assert sample_batch.status == 'paused'
    assert sample_batch.queue_position is None
    worker_pool.unregister_batch.assert_called_once_with(sample_batch.id)

    # Transition back to queued
    next_pos = queue_manager.get_next_position()
    assert state_manager.transition_state(sample_batch, 'queued', next_pos)
    db_session.refresh(sample_batch)
    assert sample_batch.status == 'queued'
    assert sample_batch.queue_position == next_pos

def test_queue_ordering(db_session, state_manager, queue_manager, worker_pool):
    """Test queue position management"""
    # Create multiple batches
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.flush()

    profile = Profile(username='test_user', niche_id=niche.id)
    db_session.add(profile)
    db_session.flush()

    batches = []
    for i in range(3):
        batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
        db_session.add(batch)
        batches.append(batch)
    db_session.flush()

    # Set queue positions
    for i, batch in enumerate(batches):
        state_manager.transition_state(batch, 'queued', i)
        db_session.flush()

    # Verify initial positions
    for i, batch in enumerate(batches):
        db_session.refresh(batch)
        assert batch.queue_position == i

    # Remove middle batch
    state_manager.transition_state(batches[1], 'paused', None)
    db_session.flush()

    # Reorder queue
    state_manager.reorder_queue()
    db_session.flush()

    # Verify reordered positions
    db_session.refresh(batches[0])
    db_session.refresh(batches[2])
    assert batches[0].queue_position == 0
    assert batches[2].queue_position == 1

def test_batch_completion(db_session, state_manager, queue_manager, sample_batch, worker_pool):
    """Test batch completion flow"""
    # Start batch
    assert state_manager.transition_state(sample_batch, 'in_progress', 0)
    db_session.flush()

    # Mark as completed
    state_manager.mark_completed(sample_batch.id)
    db_session.refresh(sample_batch)

    # Verify completion state
    assert sample_batch.status == 'done'
    assert sample_batch.queue_position is None
    assert sample_batch.completed_at is not None

def test_move_to_end(db_session, state_manager, queue_manager, sample_batch, worker_pool):
    """Test moving batch to end of queue"""
    # Start batch
    assert state_manager.transition_state(sample_batch, 'in_progress', 0)
    db_session.flush()

    # Move to end
    state_manager.move_to_end(sample_batch)
    db_session.refresh(sample_batch)

    # Verify state reset
    assert sample_batch.status == 'queued'
    assert sample_batch.queue_position > 0
    assert sample_batch.completed_profiles == 0
    assert sample_batch.successful_checks == 0
    assert sample_batch.failed_checks == 0

    # Verify profile reset
    for batch_profile in sample_batch.profiles:
        assert batch_profile.status == 'pending'
        assert not batch_profile.has_story
        assert batch_profile.error is None
        assert batch_profile.processed_at is None