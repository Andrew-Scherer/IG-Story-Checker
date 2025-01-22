"""
Test batch processor core functionality
"""

import pytest
import logging
import sys
from unittest.mock import Mock, AsyncMock
from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models.base import Base
from models.batch import Batch
from models.niche import Niche
from models.profile import Profile
# from core.batch_processor import process_batch
# from core.worker import WorkerPool

print("Starting test file execution")

# Set up logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)

print("Logger initialized")
logger.info("Logger initialized (log message)")

# Use PostgreSQL for testing
TEST_DATABASE_URI = 'postgresql://postgres:overwatch23562@localhost/ig_story_checker_test'

logger.info("Defining fixtures and test functions")

@pytest.fixture(scope='session')
def engine():
    """Create database engine"""
    logger.info("Creating database engine")
    try:
        engine = create_engine(TEST_DATABASE_URI)
        logger.info("Database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Error creating database engine: {str(e)}")
        raise

@pytest.fixture(scope='session')
def tables(engine):
    """Create all tables for testing"""
    logger.info("Creating tables")
    try:
        Base.metadata.create_all(engine)
        logger.info("Tables created successfully")
        yield
        logger.info("Dropping tables")
        Base.metadata.drop_all(engine)
        logger.info("Tables dropped successfully")
    except Exception as e:
        logger.error(f"Error in tables fixture: {str(e)}")
        raise

@pytest.fixture(scope='function')
def db_session(engine, tables):
    """Creates a new database session for each test"""
    logger.info("Creating database session")
    try:
        connection = engine.connect()
        transaction = connection.begin()
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        logger.info("Database session created successfully")
        yield session
        logger.info("Closing database session")
        session.close()
        transaction.rollback()
        connection.close()
        logger.info("Database session closed successfully")
    except Exception as e:
        logger.error(f"Error in db_session fixture: {str(e)}")
        raise

@pytest.fixture
def app(engine, db_session):
    """Create a Flask application for testing"""
    logger.info("Creating Flask application")
    try:
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        from extensions import db
        db.init_app(app)
        
        with app.app_context():
            db.session = db_session
            logger.info("Flask application created successfully")
            yield app
    except Exception as e:
        logger.error(f"Error in app fixture: {str(e)}")
        raise

def test_basic():
    """A basic test case"""
    logger.info("Starting basic test")
    assert True
    logger.info("Basic test completed")

def test_with_app(app):
    """Test using app fixture"""
    logger.info("Starting test_with_app")
    try:
        assert app is not None
        assert app.testing
        assert app.config['SQLALCHEMY_DATABASE_URI'] == TEST_DATABASE_URI
        logger.info("App checks passed")
    except Exception as e:
        logger.error(f"An error occurred in test_with_app: {str(e)}")
        raise
    logger.info("test_with_app completed successfully")

def test_with_db(db_session):
    """Test using db_session fixture"""
    logger.info("Starting test_with_db")
    try:
        assert db_session is not None
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1
        logger.info("Database session check passed")
    except Exception as e:
        logger.error(f"An error occurred in test_with_db: {str(e)}")
        raise
    logger.info("test_with_db completed successfully")

import time
from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError

def test_create_niche(db_session):
    """Test creating a simple Niche object"""
    print("Starting test_create_niche")
    logger.info("Starting test_create_niche (log message)")

    # Add event listeners for commit operations
    @event.listens_for(db_session, "before_commit")
    def before_commit(session):
        print("Before commit")
        logger.info("Before commit")

    @event.listens_for(db_session, "after_commit")
    def after_commit(session):
        print("After commit")
        logger.info("After commit")

    try:
        # Check database connection
        print("Checking database connection")
        try:
            result = db_session.execute(text("SELECT 1")).scalar()
            print(f"Database connection check result: {result}")
            logger.info(f"Database connection check result: {result}")
        except Exception as e:
            print(f"Database connection check failed: {str(e)}")
            logger.error(f"Database connection check failed: {str(e)}")
            raise

        print("Creating Niche object")
        niche = Niche(name="Test Niche")
        print("Niche object created")
        
        print("Adding Niche to session")
        db_session.add(niche)
        print("Niche added to session")
        
        print("Committing session")
        start_time = time.time()
        commit_timeout = 10  # 10 seconds timeout

        while time.time() - start_time < commit_timeout:
            try:
                db_session.commit()
                print("Session committed successfully")
                logger.info("Session committed successfully")
                break
            except SQLAlchemyError as e:
                print(f"Commit failed: {str(e)}")
                logger.error(f"Commit failed: {str(e)}")
                db_session.rollback()
                time.sleep(0.5)  # Wait for 0.5 seconds before retrying
        else:
            error_msg = "Commit operation timed out"
            print(error_msg)
            logger.error(error_msg)
            raise TimeoutError(error_msg)

        print(f"Niche created with id: {niche.id}")
        
        # Verify the niche was created
        print("Fetching Niche from database")
        fetched_niche = db_session.query(Niche).filter_by(id=niche.id).first()
        print("Niche fetched from database")
        
        assert fetched_niche is not None, "Niche not found in database"
        assert fetched_niche.name == "Test Niche", f"Expected name 'Test Niche', got '{fetched_niche.name}'"
        
        print("test_create_niche completed successfully")
        logger.info("test_create_niche completed successfully")
    except Exception as e:
        print(f"Error in test_create_niche: {str(e)}")
        logger.error(f"Error in test_create_niche: {str(e)}")
        raise
    finally:
        # Remove event listeners
        event.remove(db_session, "before_commit", before_commit)
        event.remove(db_session, "after_commit", after_commit)

logger.info("All test functions defined")

if __name__ == "__main__":
    logger.info("Running pytest directly")
    pytest.main([__file__, '-v'])
else:
    logger.info("test_batch_processor.py imported as a module")

print("Test file execution completed")
