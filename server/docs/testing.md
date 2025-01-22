# Testing Guide

## Overview

The testing suite uses pytest and follows these principles:
- Test-driven development (TDD)
- Isolated test database
- Automatic fixture cleanup
- Comprehensive API coverage

## Test Structure

```
tests/
├── conftest.py         # Shared fixtures
├── api/               # API endpoint tests
│   ├── test_niche.py
│   ├── test_profile.py
│   ├── test_batch.py
│   └── test_settings.py
├── models/           # Model unit tests
│   ├── test_niche.py
│   ├── test_profile.py
│   └── test_batch.py
└── core/            # Core logic tests
    ├── test_batch_processor.py
    └── test_worker_manager.py
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/api/test_niche.py

# Run specific test function
python -m pytest tests/api/test_niche.py::test_create_niche
```

### Test Options
```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Coverage report
pytest --cov=api tests/api/
```

## Test Database

### Configuration
Tests use a separate database (ig_story_checker_test) to avoid affecting development data.

```python
# conftest.py
TEST_DATABASE_URI = 'postgresql://postgres:password@localhost/ig_story_checker_test'
```

### Transaction Management
Each test runs in a transaction that's rolled back after completion:

```python
@pytest.fixture(scope='function')
def db_session(engine, tables):
    """Creates a new database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = scoped_session(sessionmaker(bind=connection))
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

## Writing Tests

### API Tests

```python
def test_create_niche(client, db_session):
    """Test niche creation endpoint"""
    # Arrange
    data = {
        'name': 'Test Niche',
        'daily_story_target': 20
    }
    
    # Act
    response = client.post('/api/niches', json=data)
    
    # Assert
    assert response.status_code == 201
    assert response.json['name'] == data['name']
    assert response.json['daily_story_target'] == data['daily_story_target']
```

### Model Tests

```python
def test_niche_creation(db_session):
    """Test niche model creation and validation"""
    # Arrange
    niche_data = {
        'name': 'Test Niche',
        'daily_story_target': 20
    }
    
    # Act
    niche = Niche(**niche_data)
    db_session.add(niche)
    db_session.commit()
    
    # Assert
    assert niche.id is not None
    assert niche.name == niche_data['name']
    assert niche.daily_story_target == niche_data['daily_story_target']
```

### Integration Tests

```python
def test_batch_processing_flow(client, create_niche, create_profiles):
    """Test complete batch processing flow"""
    # Setup
    niche = create_niche('Test Niche')
    profiles = create_profiles(niche.id, count=5)
    
    # Create batch
    response = client.post('/api/batches', json={
        'niche_id': niche.id
    })
    batch_id = response.json['id']
    
    # Monitor progress
    response = client.get(f'/api/batches/{batch_id}/progress')
    progress = response.json
    
    # Verify results
    response = client.get(f'/api/batches/{batch_id}/results')
    assert len(response.json) == 5
```

## Test Fixtures

### Common Fixtures

```python
# conftest.py

@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()

@pytest.fixture
def create_niche(db_session):
    """Create test niche"""
    def _create_niche(name, daily_story_target=10):
        niche = Niche(name=name, daily_story_target=daily_story_target)
        db_session.add(niche)
        db_session.commit()
        return niche
    return _create_niche

@pytest.fixture
def create_profile(db_session):
    """Create test profile"""
    def _create_profile(username, niche_id=None):
        profile = Profile(username=username, niche_id=niche_id)
        db_session.add(profile)
        db_session.commit()
        return profile
    return _create_profile
```

### Using Fixtures

```python
def test_profile_creation(client, create_niche):
    # Create niche first
    niche = create_niche('Test Niche')
    
    # Create profile in niche
    response = client.post('/api/profiles', json={
        'username': 'testuser',
        'niche_id': niche.id
    })
    
    assert response.status_code == 201
```

## Testing Best Practices

### Test Organization

1. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange
    data = {'field': 'value'}
    
    # Act
    result = function(data)
    
    # Assert
    assert result.field == 'value'
```

2. Test Naming
```python
def test_should_create_niche_with_valid_data():
def test_should_return_404_for_invalid_niche():
def test_should_validate_niche_name():
```

### Error Testing

```python
def test_error_handling(client):
    # Test missing required field
    response = client.post('/api/niches', json={})
    assert response.status_code == 400
    assert 'name is required' in response.json['error']
    
    # Test invalid data
    response = client.post('/api/niches', json={'name': ''})
    assert response.status_code == 400
    assert 'cannot be empty' in response.json['error']
```

### Mocking

```python
from unittest.mock import patch

def test_external_service(client):
    with patch('services.external.make_request') as mock_request:
        mock_request.return_value = {'status': 'success'}
        response = client.post('/api/endpoint')
        assert response.status_code == 200
```

## Common Testing Scenarios

### Authentication Testing
```python
def test_protected_endpoint(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.get('/api/protected', headers=headers)
    assert response.status_code == 200
```

### Database Constraints
```python
def test_unique_constraint(client):
    # Create first instance
    response = client.post('/api/niches', json={'name': 'Test'})
    assert response.status_code == 201
    
    # Try to create duplicate
    response = client.post('/api/niches', json={'name': 'Test'})
    assert response.status_code == 400
    assert 'already exists' in response.json['error']
```

### Batch Processing
```python
def test_batch_lifecycle(client, create_niche, create_profiles):
    # Setup test data
    niche = create_niche('Test')
    profiles = create_profiles(niche.id, count=5)
    
    # Create and verify batch
    response = client.post('/api/batches', json={'niche_id': niche.id})
    assert response.status_code == 201
    
    # Monitor progress
    batch_id = response.json['id']
    response = client.get(f'/api/batches/{batch_id}/progress')
    assert response.json['total_profiles'] == 5
