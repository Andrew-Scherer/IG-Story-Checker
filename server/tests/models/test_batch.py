"""
Tests for Batch model focusing on core functionality
"""

import pytest
from datetime import datetime, timezone
from models import Batch, Profile

def test_batch_creation_with_proxy_assignment(app, db_session, create_niche, create_profile, create_proxy_session, assign_proxy_session):
    """Test creating a new batch with proxy assignment"""
    # Create test niche
    niche = create_niche("Test Niche")
    
    # Create test profiles
    profile1 = create_profile('test1', niche_id=str(niche.id))
    profile2 = create_profile('test2', niche_id=str(niche.id))

    # Create proxy-session pair
    proxy, session = create_proxy_session()

    # Create batch
    batch = Batch(niche_id=str(niche.id), profile_ids=[profile1.id, profile2.id])
    db_session.add(batch)
    db_session.commit()

    # Assign proxy-session to batch profiles
    assign_proxy_session(batch, proxy, session)

    # Verify batch
    assert batch.id is not None
    assert batch.niche_id == str(niche.id)
    assert batch.status == 'queued'
    assert batch.total_profiles == 2
    assert batch.checked_profiles == 0
    assert batch.stories_found == 0
    assert isinstance(batch.created_at, datetime)
    assert batch.created_at.tzinfo is not None  # Just verify it's timezone-aware

    # Verify proxy assignments
    for batch_profile in batch.profiles:
        assert batch_profile.proxy_id == proxy.id
        assert batch_profile.session_id == session.id

def test_batch_status_transitions(app, db_session, create_niche, create_profile, create_proxy_session, assign_proxy_session):
    """Test batch status transitions during processing"""
    # Create test data
    niche = create_niche("Test Niche")
    profile = create_profile('test1', niche_id=str(niche.id))
    proxy, session = create_proxy_session()

    # Create and setup batch
    batch = Batch(niche_id=str(niche.id), profile_ids=[profile.id])
    db_session.add(batch)
    db_session.commit()
    assign_proxy_session(batch, proxy, session)

    # Verify initial status
    assert batch.status == 'queued'

    # Start processing
    batch.status = 'in_progress'
    db_session.commit()
    assert batch.status == 'in_progress'

    # Complete batch
    batch.status = 'done'
    db_session.commit()
    assert batch.status == 'done'

def test_batch_progress_tracking(app, db_session, create_niche, create_profile, create_proxy_session, assign_proxy_session):
    """Test tracking batch progress during story checks"""
    # Create test data
    niche = create_niche("Test Niche")
    profile1 = create_profile('test1', niche_id=str(niche.id))
    profile2 = create_profile('test2', niche_id=str(niche.id))
    proxy, session = create_proxy_session()

    # Create and setup batch
    batch = Batch(niche_id=str(niche.id), profile_ids=[profile1.id, profile2.id])
    db_session.add(batch)
    db_session.commit()
    assign_proxy_session(batch, proxy, session)

    # Simulate checking first profile (story found)
    batch.checked_profiles += 1
    batch.stories_found += 1
    db_session.commit()

    assert batch.checked_profiles == 1
    assert batch.stories_found == 1
    assert batch.completion_rate == 50.0

    # Simulate checking second profile (no story)
    batch.checked_profiles += 1
    db_session.commit()

    assert batch.checked_profiles == 2
    assert batch.stories_found == 1
    assert batch.completion_rate == 100.0
