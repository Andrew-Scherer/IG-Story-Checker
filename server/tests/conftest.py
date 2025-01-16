"""
Test Configuration
Provides fixtures and configuration for tests
"""

import pytest
from flask import Flask
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models.base import Base
from extensions import db
from api import api_bp

# Use PostgreSQL for testing
TEST_DATABASE_URI = 'postgresql://postgres:overwatch23562@localhost/ig_story_checker_test'

@pytest.fixture(scope='session')
def engine():
    """Create database engine"""
    return create_engine(TEST_DATABASE_URI)

@pytest.fixture(scope='session')
def tables(engine):
    """Create all tables for testing"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope='function')
def db_session(engine, tables):
    """Creates a new database session for each test"""
    # Connect and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Configure the session with the connection
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    
    # Start a nested transaction
    nested = connection.begin_nested()
    
    # Rollback nested transaction after each statement
    @event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            # Ensure we're in the correct state for the next transaction
            session.expire_all()
            nested.begin()

    yield session

    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def app(db_session):
    """Create Flask application for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Set up application context
    with app.app_context():
        # Use test session
        db.session = db_session
        
        # Register blueprints
        app.register_blueprint(api_bp)
        
        yield app

@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()

@pytest.fixture
def create_niche(db_session):
    """Create test niche"""
    def _create_niche(name, daily_story_target=10):
        from models.niche import Niche
        niche = Niche(name=name, daily_story_target=daily_story_target)
        db_session.add(niche)
        db_session.commit()
        return niche
    return _create_niche

@pytest.fixture
def create_profile(db_session):
    """Create test profile"""
    def _create_profile(username, niche_id=None, status='active'):
        from models.profile import Profile
        profile = Profile(username=username, niche_id=niche_id, status=status)
        db_session.add(profile)
        db_session.commit()
        return profile
    return _create_profile

@pytest.fixture
def create_batch(db_session):
    """Create test batch"""
    def _create_batch(niche_id):
        from models.batch import Batch
        batch = Batch(niche_id=niche_id)
        db_session.add(batch)
        db_session.commit()
        return batch
    return _create_batch

@pytest.fixture
def create_story(db_session):
    """Create test story result"""
    def _create_story(profile_id, batch_id):
        from models.story import StoryResult
        story = StoryResult(
            profile_id=profile_id,
            batch_id=batch_id
        )
        db_session.add(story)
        db_session.commit()
        return story
    return _create_story
