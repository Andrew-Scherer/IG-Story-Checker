import pytest
from flask import Flask
from server.app import create_app

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    yield app

def test_app_creation(app):
    assert isinstance(app, Flask)

def test_config_loading(app):
    assert app.config['TESTING'] == True

def test_database_initialization(app):
    with app.app_context():
        db = app.extensions['sqlalchemy']
        assert db.engine is not None

def test_error_handler(app, client):
    with app.test_request_context():
        @app.route('/test_error')
        def test_error():
            raise Exception('Test error')
        
        # Create a test client and make the request
        test_client = app.test_client()
        response = test_client.get('/test_error')
        assert response.status_code == 500
        assert 'error' in response.get_json()

def test_worker_pool_initialization(app):
    assert hasattr(app, 'worker_pool')

def test_blueprint_registration(app):
    assert 'api' in app.blueprints

def test_processing_state(app):
    assert hasattr(app, 'processing')
    assert app.processing == False

def test_cors_enabled(app):
    assert 'cors' in app.extensions

# Add more specific tests based on your application's functionality
