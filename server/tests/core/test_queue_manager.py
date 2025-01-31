"""
Test Queue Manager
Tests for queue position management and batch promotion
"""

import pytest
from datetime import datetime, UTC
from models import db, Batch, Profile, Niche
from services.queue_manager import queue_manager
from services.batch_log_service import BatchLogService

@pytest.fixture
def sample_batches(db_session):
    """Create sample batches for testing"""
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username='test_user', niche_id=niche.id)
    db_session.add(profile)
    db_session.commit()

    batches = []
    for i in range(3):
        batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
        db_session.add(batch)
        batches.append(batch)
    db_session.commit()

    return batches

def test_get_next_position(app, db_session, sample_batches):
    """Test next queue position calculation"""
    with app.app_context():
        # Initial position should be 1
        assert queue_manager.get_next_position() == 1

        # Set positions for existing batches
        for i, batch in enumerate(sample_batches):
            batch.queue_position = i + 1
        db_session.commit()

        # Next position should be after last batch
        assert queue_manager.get_next_position() == 4

def test_promote_next_batch(app, db_session, sample_batches):
    """Test batch promotion logic"""
    with app.app_context():
        # Set up batch positions
        sample_batches[0].status = 'queued'
        sample_batches[0].queue_position = 1
        sample_batches[1].status = 'queued'
        sample_batches[1].queue_position = 2
        db_session.commit()

        # Promote first batch
        promoted = queue_manager.promote_next_batch()
        assert promoted is not None
        assert promoted.id == sample_batches[0].id

        # Verify promotion
        db_session.refresh(sample_batches[0])
        assert sample_batches[0].status == 'in_progress'
        assert sample_batches[0].queue_position == 0

def test_schedule_queue_update(app, db_session, sample_batches):
    """Test queue update scheduling"""
    with app.app_context():
        # Set up batch positions
        sample_batches[0].status = 'queued'
        sample_batches[0].queue_position = 2
        sample_batches[1].status = 'queued'
        sample_batches[1].queue_position = 4
        db_session.commit()

        # Schedule update
        queue_manager.schedule_queue_update()

        # Verify reordering
        db_session.refresh(sample_batches[0])
        db_session.refresh(sample_batches[1])
        assert sample_batches[0].queue_position == 1
        assert sample_batches[1].queue_position == 2

def test_get_running_batch(app, db_session, sample_batches):
    """Test getting currently running batch"""
    with app.app_context():
        # Initially no running batch
        assert queue_manager.get_running_batch() is None

        # Set a running batch
        sample_batches[0].status = 'in_progress'
        sample_batches[0].queue_position = 0
        db_session.commit()

        # Verify running batch
        running = queue_manager.get_running_batch()
        assert running is not None
        assert running.id == sample_batches[0].id

def test_automatic_promotion(app, db_session, sample_batches):
    """Test automatic batch promotion after completion"""
    with app.app_context():
        # Set up batches
        sample_batches[0].status = 'in_progress'
        sample_batches[0].queue_position = 0
        sample_batches[1].status = 'queued'
        sample_batches[1].queue_position = 1
        db_session.commit()

        # Complete first batch
        queue_manager.state_manager.mark_completed(sample_batches[0].id)
        db_session.commit()

        # Schedule queue update
        queue_manager.schedule_queue_update()

        # Verify promotion
        db_session.refresh(sample_batches[1])
        assert sample_batches[1].queue_position == 0
        assert sample_batches[1].status == 'in_progress'
