"""
Test Configuration
Provides fixtures and configuration for tests
"""

import os
import pytest
from sqlalchemy import event, text
from sqlalchemy.orm import sessionmaker
from app import create_app
from models import db as _db

# Use PostgreSQL for testing
TEST_DATABASE_URI = 'postgresql://postgres:overwatch23562@localhost/ig_story_checker_test'

@pytest.fixture(scope='session')
def app():
    """Create application for tests"""
    # Override config for testing
    config_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app(config_override)
    
    # Create context
    ctx = app.app_context()
    ctx.push()
    
    yield app
    
    ctx.pop()

@pytest.fixture(scope='session')
def db(app):
    """Create database for tests"""
    _db.drop_all()
    _db.create_all()
    
    yield _db
    
    _db.drop_all()

@pytest.fixture(scope='function')
def db_session(db):
    """Provide an isolated database session for each test.
    
    This fixture:
    1. Creates a new transaction
    2. Yields the session for test use
    3. Rolls back the transaction after test
    4. Cleans up tables if any commits occurred
    """
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Create session factory
    Session = sessionmaker(bind=connection)
    
    # Create session for this test
    session = Session()

    # Begin a nested transaction (using SAVEPOINT)
    nested = connection.begin_nested()

    # If the session commits, the nested transaction will be used
    # and the outer transaction will remain open
    @event.listens_for(session, 'after_transaction_end')
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()
    
    yield session
    
    # Rollback everything
    session.close()
    transaction.rollback()
    connection.close()
    
    # Clean up tables to handle any committed data
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(text(f'TRUNCATE TABLE {table.name} CASCADE'))
    db.session.commit()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
