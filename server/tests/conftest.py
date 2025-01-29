import pytest
import sys
import os
from sqlalchemy.orm import sessionmaker

# Add the server directory to the Python path
server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, server_dir)

from app import create_app
from extensions import db as _db
from config import TestingConfig

@pytest.fixture(scope='session')
def app():
    app = create_app(TestingConfig)
    return app

@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def db_session(db):
    connection = db.engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    transaction.rollback()
    connection.close()
    session.close()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()
