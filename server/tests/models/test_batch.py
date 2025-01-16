"""
Test Batch Models
Tests batch processing state and profile results tracking
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from models.batch import Batch, BatchProfile
from models.niche import Niche
from models.profile import Profile

def test_create_batch(db_session):
    """Test basic batch creation"""
    # Create niche first
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    # Create batch
    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    assert batch.id is not None
    assert batch.niche_id == niche.id
    assert batch.status == 'pending'
    assert batch.start_time is None
    assert batch.end_time is None
    assert batch.total_profiles == 0
    assert batch.completed_profiles == 0
    assert batch.successful_checks == 0
    assert batch.failed_checks == 0
    assert isinstance(batch.created_at, datetime)
    assert isinstance(batch.updated_at, datetime)

def test_batch_niche_relationship(db_session):
    """Test batch relationship with niche"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    assert batch.niche == niche
    assert batch in niche.batches

def test_batch_status_transitions(db_session):
    """Test batch status transitions"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    # Test start
    batch.start(session=db_session)
    assert batch.status == 'running'
    assert batch.start_time is not None
    assert batch.end_time is None

    # Test complete
    batch.complete(session=db_session)
    assert batch.status == 'completed'
    assert batch.end_time is not None

    # Test fail
    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()
    
    batch.start()
    batch.fail("Test error", session=db_session)
    assert batch.status == 'failed'
    assert batch.end_time is not None

def test_batch_profile_creation(db_session):
    """Test creating batch profiles"""
    # Setup
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username="test_user", niche=niche)
    db_session.add(profile)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    # Create batch profile
    batch_profile = BatchProfile(
        batch_id=batch.id,
        profile_id=profile.id
    )
    db_session.add(batch_profile)
    db_session.commit()

    assert batch_profile.id is not None
    assert batch_profile.batch_id == batch.id
    assert batch_profile.profile_id == profile.id
    assert batch_profile.status == 'pending'
    assert batch_profile.has_story is False
    assert batch_profile.error is None
    assert batch_profile.processed_at is None

def test_batch_profile_completion(db_session):
    """Test batch profile completion flow"""
    # Setup
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username="test_user", niche=niche)
    db_session.add(profile)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    batch_profile = BatchProfile(
        batch_id=batch.id,
        profile_id=profile.id
    )
    db_session.add(batch_profile)
    db_session.commit()

    # Test completion with story
    batch_profile.complete(has_story=True, session=db_session)
    assert batch_profile.status == 'completed'
    assert batch_profile.has_story is True
    assert batch_profile.processed_at is not None
    assert batch_profile.error is None

    # Verify batch stats updated
    batch.update_stats(session=db_session)
    assert batch.total_profiles == 1
    assert batch.completed_profiles == 1
    assert batch.successful_checks == 1
    assert batch.failed_checks == 0

def test_batch_profile_failure(db_session):
    """Test batch profile failure handling"""
    # Setup
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username="test_user", niche=niche)
    db_session.add(profile)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    batch_profile = BatchProfile(
        batch_id=batch.id,
        profile_id=profile.id
    )
    db_session.add(batch_profile)
    db_session.commit()

    # Test failure
    error_msg = "Test error message"
    batch_profile.fail(error_msg, session=db_session)
    assert batch_profile.status == 'failed'
    assert batch_profile.error == error_msg
    assert batch_profile.processed_at is not None
    assert batch_profile.has_story is False

    # Verify batch stats updated
    batch.update_stats()
    assert batch.total_profiles == 1
    assert batch.completed_profiles == 0
    assert batch.successful_checks == 0
    assert batch.failed_checks == 1

def test_batch_stats_multiple_profiles(db_session):
    """Test batch statistics with multiple profiles"""
    # Setup
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    # Create multiple profiles with different outcomes
    profiles = []
    for i in range(5):
        profile = Profile(username=f"test_user_{i}", niche=niche)
        db_session.add(profile)
        db_session.commit()
        profiles.append(profile)

    # Add batch profiles with different states
    batch_profiles = []
    for i, profile in enumerate(profiles):
        bp = BatchProfile(batch_id=batch.id, profile_id=profile.id)
        db_session.add(bp)
        db_session.commit()
        batch_profiles.append(bp)

    # Set different states
    batch_profiles[0].complete(has_story=True, session=db_session)  # Success with story
    batch_profiles[1].complete(has_story=False, session=db_session)  # Success without story
    batch_profiles[2].fail("Error 1", session=db_session)  # Failed
    batch_profiles[3].fail("Error 2", session=db_session)  # Failed
    # Last one remains pending

    # Verify stats
    batch.update_stats()
    assert batch.total_profiles == 5
    assert batch.completed_profiles == 2
    assert batch.successful_checks == 1
    assert batch.failed_checks == 2

def test_get_active_batch_for_niche(db_session):
    """Test getting active batch for niche"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    # Create completed batch
    completed_batch = Batch(niche_id=niche.id)
    db_session.add(completed_batch)
    db_session.commit()
    completed_batch.start(session=db_session)
    completed_batch.complete(session=db_session)

    # Create running batch
    running_batch = Batch(niche_id=niche.id)
    db_session.add(running_batch)
    db_session.commit()
    running_batch.start(session=db_session)

    # Test get active
    active = Batch.get_active_for_niche(niche.id, session=db_session)
    assert active == running_batch

def test_batch_serialization(db_session):
    """Test batch serialization to dictionary"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    batch_dict = batch.to_dict()
    assert isinstance(batch_dict, dict)
    assert batch_dict['id'] == batch.id
    assert batch_dict['niche_id'] == niche.id
    assert batch_dict['status'] == 'pending'
    assert batch_dict['start_time'] is None
    assert batch_dict['end_time'] is None
    assert batch_dict['total_profiles'] == 0
    assert batch_dict['completed_profiles'] == 0
    assert batch_dict['successful_checks'] == 0
    assert batch_dict['failed_checks'] == 0
    assert 'created_at' in batch_dict
    assert 'updated_at' in batch_dict

def test_batch_profile_serialization(db_session):
    """Test batch profile serialization to dictionary"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username="test_user", niche=niche)
    db_session.add(profile)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    batch_profile = BatchProfile(
        batch_id=batch.id,
        profile_id=profile.id
    )
    db_session.add(batch_profile)
    db_session.commit()

    bp_dict = batch_profile.to_dict()
    assert isinstance(bp_dict, dict)
    assert bp_dict['id'] == batch_profile.id
    assert bp_dict['batch_id'] == batch.id
    assert bp_dict['profile_id'] == profile.id
    assert bp_dict['status'] == 'pending'
    assert bp_dict['has_story'] is False
    assert bp_dict['error'] is None
    assert bp_dict['processed_at'] is None
    assert 'created_at' in bp_dict
    assert 'updated_at' in bp_dict

def test_batch_requires_niche(db_session):
    """Test batch requires valid niche"""
    batch = Batch(niche_id=None)
    db_session.add(batch)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

def test_batch_profile_requires_batch_and_profile(db_session):
    """Test batch profile requires both batch and profile"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username="test_user", niche=niche)
    db_session.add(profile)
    db_session.commit()

    batch = Batch(niche_id=niche.id)
    db_session.add(batch)
    db_session.commit()

    # Test missing batch_id
    bp = BatchProfile(batch_id=None, profile_id=profile.id)
    db_session.add(bp)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Test missing profile_id
    bp = BatchProfile(batch_id=batch.id, profile_id=None)
    db_session.add(bp)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
