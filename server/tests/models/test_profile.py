import os
import sys
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Add the server directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.profile import Profile
from models.niche import Niche

def test_create_profile(db_session):
    """Test basic profile creation with required fields"""
    profile = Profile(username="test_create_user")
    db_session.add(profile)
    db_session.commit()

    assert profile.id is not None
    assert profile.username == "test_create_user"
    assert profile.status == "active"  # Default status
    assert profile.total_checks == 0
    assert profile.total_detections == 0

def test_username_unique_constraint(db_session):
    """Test that usernames must be unique"""
    profile1 = Profile(username="test_unique_user")
    db_session.add(profile1)
    db_session.commit()

    profile2 = Profile(username="test_unique_user")
    db_session.add(profile2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_profile_niche_relationship(db_session):
    """Test profile can be assigned to a niche"""
    niche = Niche(name="Fitness")
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username="test_niche_user", niche=niche)
    db_session.add(profile)
    db_session.commit()

    assert profile.niche_id == niche.id
    assert profile.niche.name == "Fitness"

def test_profile_status_validation(db_session):
    """Test profile status must be valid"""
    with pytest.raises(ValueError) as exc_info:
        Profile(username="test_status_user", status="invalid")
    assert "Invalid status" in str(exc_info.value)
    assert "active, deleted, suspended" in str(exc_info.value)

def test_profile_check_tracking(db_session):
    """Test tracking of story checks and detections"""
    profile = Profile(username="test_tracking_user")
    db_session.add(profile)
    db_session.commit()

    # Simulate a story check without detection
    profile.record_check()
    assert profile.total_checks == 1
    assert profile.total_detections == 0
    assert profile.last_checked is not None

    # Simulate a story check with detection
    profile.record_check(story_detected=True)
    assert profile.total_checks == 2
    assert profile.total_detections == 1
    assert profile.last_detected is not None

def test_profile_soft_delete(db_session):
    """Test profile can be soft deleted"""
    profile = Profile(username="test_delete_user")
    db_session.add(profile)
    db_session.commit()

    original_updated_at = profile.updated_at
    profile.soft_delete()
    assert profile.status == "deleted"
    assert profile.updated_at > original_updated_at

    # Profile should still be queryable
    assert db_session.query(Profile).filter_by(username="test_delete_user").first() is not None

def test_profile_reactivation(db_session):
    """Test deleted profile can be reactivated"""
    profile = Profile(username="test_reactivate_user")
    db_session.add(profile)
    db_session.commit()

    profile.soft_delete()
    original_updated_at = profile.updated_at
    profile.reactivate()
    assert profile.status == "active"
    assert profile.updated_at > original_updated_at

def test_profile_timestamps(db_session):
    """Test profile timestamps are automatically set"""
    profile = Profile(username="test_timestamps_user")
    db_session.add(profile)
    db_session.commit()

    assert isinstance(profile.created_at, datetime)
    assert isinstance(profile.updated_at, datetime)

    original_updated_at = profile.updated_at
    profile.record_check()
    db_session.commit()

    assert profile.updated_at > original_updated_at

def test_profile_batch_relationship(db_session):
    """Test profile maintains batch processing relationship"""
    profile = Profile(username="test_batch_user")
    db_session.add(profile)
    db_session.commit()

    # Test BatchProfile relationship exists
    assert hasattr(profile, 'batch_profiles')
    assert profile.batch_profiles == []  # Should start empty

def test_check_success_rate(db_session):
    """Test success rate calculation"""
    profile = Profile(username="test_success_rate_user")
    db_session.add(profile)
    db_session.commit()

    # No checks yet
    assert profile.detection_rate == 0.0

    # One check, no detection
    profile.record_check(story_detected=False)
    assert profile.detection_rate == 0.0

    # Two checks, one detection
    profile.record_check(story_detected=True)
    assert profile.detection_rate == 50.0

    # Three checks, two detections
    profile.record_check(story_detected=True)
    assert profile.detection_rate == pytest.approx(66.67, rel=0.01)

def test_to_dict_method(db_session):
    """Test profile serialization to dictionary"""
    profile = Profile(username="test_dict_user")
    db_session.add(profile)
    db_session.commit()

    profile_dict = profile.to_dict()
    
    # Check all required fields are present
    assert isinstance(profile_dict, dict)
    assert profile_dict['username'] == "test_dict_user"
    assert profile_dict['status'] == "active"
    assert profile_dict['total_checks'] == 0
    assert profile_dict['total_detections'] == 0
    assert profile_dict['detection_rate'] == 0.0
    assert profile_dict['niche_id'] is None
    assert 'created_at' in profile_dict
    assert 'updated_at' in profile_dict

def test_profile_update(db_session):
    """Test updating profile attributes"""
    profile = Profile(username="old_username")
    db_session.add(profile)
    db_session.commit()

    # Update username
    profile.username = "new_username"
    db_session.commit()

    updated_profile = db_session.get(Profile, profile.id)
    assert updated_profile.username == "new_username"
    assert updated_profile.updated_at > updated_profile.created_at

def test_is_active_property(db_session):
    """Test is_active property behavior"""
    profile = Profile(username="test_active_user")
    db_session.add(profile)
    db_session.commit()

    assert profile.is_active is True

    profile.soft_delete()
    assert profile.is_active is False

    profile.reactivate()
    assert profile.is_active is True

def test_username_validation(db_session):
    """Test username validation"""
    # Test empty username
    with pytest.raises(IntegrityError):
        profile = Profile(username="")
        db_session.add(profile)
        db_session.flush()  # Force DB interaction without committing
        
    db_session.rollback()  # Clean up after the error

    # Test null username
    with pytest.raises(IntegrityError):
        profile = Profile(username=None)
        db_session.add(profile)
        db_session.flush()  # Force DB interaction without committing
        
    db_session.rollback()  # Clean up after the error
