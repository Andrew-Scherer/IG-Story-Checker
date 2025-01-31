import pytest
import sys
import os
import logging
from unittest.mock import MagicMock
from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Add the server directory to the Python path
server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, server_dir)

from app import create_app
from extensions import db as _db
from config import TestingConfig

# Mock logging setup for tests
def mock_setup_blueprint_logging(blueprint, name):
    """Mock logging setup for tests"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # Clear any existing handlers
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    blueprint.logger = logger
    return logger

def mock_setup_component_logging(name):
    """Mock component logging setup for tests"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # Clear any existing handlers
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Mock the logging setup functions
import config.logging_config
config.logging_config.setup_blueprint_logging = mock_setup_blueprint_logging
config.logging_config.setup_component_logging = mock_setup_component_logging

@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing"""
    app = create_app(TestingConfig)
    
    # Create a new engine for testing
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    app.config['SQLALCHEMY_ENGINE'] = engine
    
    # Configure session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    # Override the Flask-SQLAlchemy session
    _db.session = Session
    
    return app

@pytest.fixture(scope='function')
def db(app):
    """Set up database for testing"""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.close()
        _db.drop_all()

@pytest.fixture(scope='function')
def db_session(app, db):
    """Create database session for testing"""
    with app.app_context():
        # Start a transaction
        connection = db.engine.connect()
        transaction = connection.begin()

        # Create a session bound to the connection
        session_factory = sessionmaker(bind=connection)
        session = session_factory()

        # Make the session available to the app
        old_session = db.session
        db.session = session

        yield session

        # Clean up
        session.close()
        transaction.rollback()
        connection.close()
        db.session = old_session

@pytest.fixture(scope='function')
def client(app):
    """Create Flask test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def worker_pool(db_session):
    """Mock worker pool for testing
    
    Args:
        db_session: Database session from fixture
        
    Returns:
        MagicMock: Mocked worker pool with test-appropriate methods
    """
    pool = MagicMock()
    
    # Configure mock methods with proper returns
    pool.register_batch = MagicMock(return_value=True)
    pool.unregister_batch = MagicMock(return_value=True)
    pool.submit = MagicMock(side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs))
    
    # Add worker pool to current app without new context
    current_app.worker_pool = pool
    
    # Yield outside any context
    yield pool
    
    # Clean up using existing session
    if hasattr(current_app, 'worker_pool'):
        delattr(current_app, 'worker_pool')
