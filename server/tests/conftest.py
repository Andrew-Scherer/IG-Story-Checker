"""
"""

import sys
import os
import pytest

# Add server directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import uuid
from datetime import datetime, UTC
from unittest.mock import Mock
from flask import Flask, current_app
from server.extensions import db
from server import services
from server.services import batch_log_service, batch_manager
from server.models import Batch, Niche, Profile, BatchLog, Proxy

def create_mock_niche(niche_id=None, name="Test Niche"):
    """Create a mock niche with consistent to_dict() behavior"""
    if not niche_id:
        niche_id = str(uuid.uuid4())
        
    mock_niche = Mock(spec=server.models.Niche)
    mock_niche.id = niche_id
    mock_niche.name = name
    mock_niche.to_dict.return_value = {
        'id': niche_id,
        'name': name
    }
    return mock_niche

def create_mock_profile(profile_id=None, username="test_user"):
    """Create a mock profile with consistent to_dict() behavior"""
    if not profile_id:
        profile_id = str(uuid.uuid4())
        
    mock_profile = Mock(spec=server.models.Profile)
    mock_profile.id = profile_id
    mock_profile.username = username
    mock_profile.to_dict.return_value = {
        'id': profile_id,
        'username': username
    }
    return mock_profile

# Store mock batches and logs to persist state
mock_batches = {}
mock_logs = {}

def mock_create_log(batch_id, message, log_type='STATE_CHANGE'):
    """Create and store a mock log entry"""
    if batch_id not in mock_logs:
        mock_logs[batch_id] = []
    log = {
        'batch_id': batch_id,
        'message': message,
        'type': log_type,
        'timestamp': datetime.now(UTC).isoformat()
    }
    # Create a mock BatchLog object
    mock_log = Mock(spec=BatchLog)
    mock_log.to_dict.return_value = log
    mock_logs[batch_id].append(mock_log)
    return mock_log

def mock_get_batch(batch_id):
    """Get or create a mock batch with persistent state"""
    if batch_id not in mock_batches:
        mock_batches[batch_id] = create_mock_batch(batch_id=batch_id, status='queued')
    return mock_batches[batch_id]

def create_mock_batch(batch_id=None, status='queued', position=None):
    """Create a mock batch with consistent to_dict() behavior"""
    if not batch_id:
        batch_id = str(uuid.uuid4())
        
    mock_batch = Mock(spec=server.models.Batch)
    mock_batch.id = batch_id
    mock_batch.status = status
    mock_batch.position = position
    mock_batch.to_dict.return_value = {
        'id': batch_id,
        'status': status,
        'position': position,
        'niche_id': str(uuid.uuid4()),
        'total_profiles': 1,
        'completed_profiles': 0
    }
    return mock_batch

@pytest.fixture(scope="session")
def app():
    """Creates and configures a new app instance for each test session."""
    from server.app import create_app
    from server.config import TestingConfig
    
    # Override database URI to use SQLite for testing
    test_config = TestingConfig()
    test_config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    app = create_app(test_config)
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost:5000'
    
    # For real_db tests, maintain a single app context throughout the session
    ctx = app.app_context()
    ctx.push()
    
    # Create tables in test database
    # Note: db is already initialized in create_app()
    db.create_all()
    
    yield app
    
    # Cleanup
    db.session.remove()
    db.drop_all()
    ctx.pop()

@pytest.fixture(scope="session")
def client(app):
    """Provides a test client for the app."""
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app):
    """Provides a database session for tests."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = db.session  # Use Flask-SQLAlchemy's built-in session handling
        session.begin_nested()  # Start a nested transaction for rollback support

        yield session  # Provide session to tests

        session.rollback()
        session.remove()  # Cleanup session
        transaction.rollback()
        connection.close()

@pytest.fixture
def test_niche(request, app):
    """Creates a niche for use in tests.
    For @real_db tests, creates a real niche in the database.
    For other tests, creates a mock niche."""
    if request.node.get_closest_marker('real_db'):
        with app.app_context():
            niche = Niche(
                id=str(uuid.uuid4()),
                name="Test Niche",
                description="Test niche for real db tests"
            )
            db.session.add(niche)
            db.session.commit()
            return niche
    else:
        return create_mock_niche()

@pytest.fixture
def test_profile(request, app):
    """Creates a profile for use in tests.
    For @real_db tests, creates a real profile in the database.
    For other tests, creates a mock profile."""
    if request.node.get_closest_marker('real_db'):
        with app.app_context():
            profile = Profile(
                id=str(uuid.uuid4()),
                username="test_user",
                niche_id=str(uuid.uuid4())
            )
            db.session.add(profile)
            db.session.commit()
            return profile
    else:
        return create_mock_profile()

@pytest.fixture
def test_batch(request, app):
    """Creates a batch for use in tests.
    For @real_db tests, creates a real batch in the database.
    For other tests, creates a mock batch."""
    if request.node.get_closest_marker('real_db'):
        with app.app_context():
            # Create a real batch in the database
            batch = Batch(
                niche_id=str(uuid.uuid4()),
                profile_ids=[str(uuid.uuid4())],
                total_profiles=1,
                completed_profiles=0,
                status='queued'
            )
            db.session.add(batch)
            db.session.commit()
            return batch
    else:
        # Create a mock batch for non-real_db tests
        batch = create_mock_batch()
        mock_batches[batch.id] = batch  # Store in mock_batches for state persistence
        return batch

@pytest.fixture(autouse=True)
def mock_flask_and_db(request, app, monkeypatch):
    """Mock Flask current_app and db for all tests"""
    
    # Skip mocking for tests marked with real_db
    if request.node.get_closest_marker('real_db'):
        # For real_db tests, only mock the logger to prevent excessive logging
        mock_app = Mock()
        mock_app.logger = Mock()
        mock_app.logger.info = Mock()
        mock_app.logger.error = Mock()
        mock_app.logger.warning = Mock()
        monkeypatch.setattr('server.services.batch_log_service.current_app', mock_app)
        monkeypatch.setattr('server.core.batch_processor.current_app', mock_app)
        return
        
    # For non-real_db tests, use full mocking as before
    mock_app = Mock()
    mock_app.logger = Mock()
    mock_app.logger.info = Mock()
    mock_app.logger.error = Mock()
    mock_app.logger.warning = Mock()
    
    monkeypatch.setattr('server.services.batch_log_service.current_app', mock_app)
    monkeypatch.setattr('server.core.batch_processor.current_app', mock_app)

    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.flush = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()
    
    def mock_get(model_class, id):
        if model_class == server.models.Batch:
            return mock_get_batch(id)
        elif model_class == server.models.Niche:
            return create_mock_niche(niche_id=id)
        elif model_class == server.models.Profile:
            return create_mock_profile(profile_id=id)
        return None
    mock_session.get = Mock(side_effect=mock_get)
    
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.first.return_value = None
    mock_query.all.return_value = []
    mock_query.scalar.return_value = 0
    mock_query.count.return_value = 0
    mock_query.limit = Mock(return_value=mock_query)
    mock_query.offset = Mock(return_value=mock_query)

    mock_execute_result = Mock()
    mock_execute_result.scalar.return_value = None
    mock_session.execute = Mock(return_value=mock_execute_result)
    mock_session.query.return_value = mock_query

    monkeypatch.setattr(Proxy, 'query', mock_query)
    monkeypatch.setattr('server.services.batch_log_service.db.session', mock_session)
    monkeypatch.setattr('server.services.batch_manager.db.session', mock_session)
    monkeypatch.setattr('server.models.db.session', mock_session)
    monkeypatch.setattr('server.extensions.db.session', mock_session)

    return mock_session
