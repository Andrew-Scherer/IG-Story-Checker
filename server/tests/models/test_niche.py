import os
import sys
import pytest
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import event
from contextlib import contextmanager
from threading import Timer

# Add the server directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.niche import Niche
from models.profile import Profile

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@contextmanager
def db_session_commit_timeout(session, timeout_seconds=5):
    """Context manager to add a timeout to database commit operations."""
    def timeout_handler():
        raise TimeoutError("Database commit operation timed out")

    timer = Timer(timeout_seconds, timeout_handler)
    timer.start()
    try:
        yield
    finally:
        timer.cancel()

def add_sqlalchemy_event_listeners(session):
    """Add SQLAlchemy event listeners for detailed logging."""
    @event.listens_for(session, "before_commit")
    def before_commit(session):
        logger.debug("Before commit")

    @event.listens_for(session, "after_commit")
    def after_commit(session):
        logger.debug("After commit")

    @event.listens_for(session, "after_rollback")
    def after_rollback(session):
        logger.debug("After rollback")

def test_create_niche(db_session):
    """Test basic niche creation with required fields"""
    add_sqlalchemy_event_listeners(db_session)
    
    niche = Niche(name="Fitness_Create")
    db_session.add(niche)
    
    try:
        with db_session_commit_timeout(db_session):
            db_session.commit()
    except TimeoutError:
        logger.error("Commit operation timed out")
        db_session.rollback()
        pytest.fail("Database commit timed out")
    except SQLAlchemyError as e:
        logger.error(f"An error occurred during commit: {str(e)}")
        db_session.rollback()
        pytest.fail(f"Database error: {str(e)}")

    assert niche.id is not None
    assert niche.name == "Fitness_Create"
    assert niche.order == 0  # Default order
    assert isinstance(niche.created_at, datetime)
    assert isinstance(niche.updated_at, datetime)

def test_niche_name_unique_constraint(db_session):
    """Test that niche names must be unique"""
    niche1 = Niche(name="Fitness_Unique")
    db_session.add(niche1)
    db_session.commit()

    niche2 = Niche(name="Fitness_Unique")
    db_session.add(niche2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_niche_name_validation(db_session):
    """Test niche name validation"""
    # Test empty name
    with pytest.raises(IntegrityError):
        niche = Niche(name="")
        db_session.add(niche)
        db_session.flush()
    db_session.rollback()

    # Test null name
    with pytest.raises(IntegrityError):
        niche = Niche(name=None)
        db_session.add(niche)
        db_session.flush()
    db_session.rollback()

def test_niche_profile_relationship(db_session):
    """Test niche can have multiple profiles"""
    niche = Niche(name="Fitness_Relationship")
    db_session.add(niche)
    db_session.commit()

    # Create profiles and assign to niche
    profile1 = Profile(username="fitness_user1", niche=niche)
    profile2 = Profile(username="fitness_user2", niche=niche)
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Test relationship
    assert len(niche.profiles) == 2
    assert niche.profiles[0].username == "fitness_user1"
    assert niche.profiles[1].username == "fitness_user2"

def test_niche_display_order(db_session):
    """Test niche display order management"""
    # Create niches with specific orders
    niche1 = Niche(name="Fitness_Order", order=1)
    niche2 = Niche(name="Fashion", order=2)
    niche3 = Niche(name="Food", order=3)
    db_session.add_all([niche1, niche2, niche3])
    db_session.commit()

    # Test ordering
    niches = db_session.query(Niche).order_by(Niche.order).all()
    assert [n.name for n in niches] == ["Fitness_Order", "Fashion", "Food"]

    # Test reordering
    niche1.order = 3
    niche2.order = 1
    niche3.order = 2
    db_session.commit()

    niches = db_session.query(Niche).order_by(Niche.order).all()
    assert [n.name for n in niches] == ["Fashion", "Food", "Fitness_Order"]

def test_niche_deletion_profile_handling(db_session):
    """Test profile handling when niche is deleted"""
    niche = Niche(name="Fitness_Delete")
    db_session.add(niche)
    db_session.commit()

    # Create profiles in the niche
    profile1 = Profile(username="fitness_user1", niche=niche)
    profile2 = Profile(username="fitness_user2", niche=niche)
    db_session.add_all([profile1, profile2])
    db_session.commit()

    # Delete niche
    db_session.delete(niche)
    db_session.commit()

    # Verify profiles still exist but without niche
    profiles = db_session.query(Profile).all()
    assert len(profiles) == 2
    assert all(p.niche_id is None for p in profiles)

def test_niche_to_dict(db_session):
    """Test niche serialization to dictionary"""
    niche = Niche(name="Fitness_Dict", order=1)
    db_session.add(niche)
    db_session.commit()

    niche_dict = niche.to_dict()
    
    assert isinstance(niche_dict, dict)
    assert niche_dict['name'] == "Fitness_Dict"
    assert niche_dict['order'] == 1
    assert 'id' in niche_dict
    assert 'created_at' in niche_dict
    assert 'updated_at' in niche_dict

def test_niche_update(db_session):
    """Test updating niche attributes"""
    niche = Niche(name="Fitness_Update")
    db_session.add(niche)
    db_session.commit()

    original_updated_at = niche.updated_at

    # Update name
    niche.name = "Health & Fitness"
    db_session.commit()

    assert niche.name == "Health & Fitness"
    assert niche.updated_at > original_updated_at

def test_niche_cascade_profile_updates(db_session):
    """Test cascading updates to profiles"""
    niche = Niche(name="Fitness_Cascade")
    db_session.add(niche)
    db_session.commit()

    # Add profiles
    profiles = [
        Profile(username=f"fitness_user{i}", niche=niche)
        for i in range(3)
    ]
    db_session.add_all(profiles)
    db_session.commit()

    # Update niche
    niche.name = "Health & Fitness"
    db_session.commit()

    # Verify profiles maintained relationship
    updated_profiles = db_session.query(Profile).filter_by(niche_id=niche.id).all()
    assert len(updated_profiles) == 3
    assert all(p.niche.name == "Health & Fitness" for p in updated_profiles)
