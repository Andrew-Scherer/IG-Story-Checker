# Testing Guide

## Core Principles

1. **Consistent Database Handling**
   - One database per test session
   - Managed by fixtures
   - Clean state for each test

2. **Clear Test Organization**
   - API tests in tests/api/
   - Service tests in tests/services/
   - Core tests in tests/core/

3. **Proper Test Isolation**
   - Each test runs independently
   - No shared state
   - Clean setup and teardown

## Database Testing

### Using the Real Database

For tests that need database access:

```python
@pytest.mark.real_db
def test_user_creation(app, db_session):
    # The app fixture provides:
    # - Test database configuration
    # - Active Flask context
    # - Clean database for each session
    
    # The db_session fixture provides:
    # - Transaction management
    # - Automatic rollback
    # - Clean state for each test
    
    user = User(name="Test")
    db_session.add(user)
    db_session.commit()
    
    assert User.query.count() == 1
```

Key Points:
- Use @pytest.mark.real_db marker
- Let fixtures manage the database
- Each test runs in a transaction
- Transactions roll back automatically

### Test Database Configuration

The test database uses SQLite in memory:

```python
# config.py
class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
```

Benefits:
- Fast execution
- No external dependencies
- Fresh database for each session
- No cleanup needed

## API Testing

### Testing Endpoints

```python
@pytest.mark.real_db
def test_create_user(client):
    # Test request validation
    response = client.post('/api/users', json={})
    assert response.status_code == 400
    assert 'name is required' in response.get_json()['error']
    
    # Test successful creation
    response = client.post('/api/users', json={'name': 'Test'})
    assert response.status_code == 201
    assert response.get_json()['name'] == 'Test'
```

Key Points:
- Test input validation
- Test success cases
- Test error responses
- Verify response format

### Testing Authentication

```python
@pytest.mark.real_db
def test_protected_endpoint(client, auth_headers):
    # Test without auth
    response = client.get('/api/protected')
    assert response.status_code == 401
    
    # Test with auth
    response = client.get('/api/protected', headers=auth_headers)
    assert response.status_code == 200
```

## Service Testing

### Testing Business Logic

```python
@pytest.mark.real_db
def test_user_service(db_session):
    # Test service methods
    user = UserService.create_user(name="Test")
    assert user.name == "Test"
    
    # Test business rules
    with pytest.raises(ValueError):
        UserService.create_user(name="")
```

Key Points:
- Test business rules
- Test validation logic
- Test error handling
- Use appropriate assertions

## Mocking

### When to Mock

Mock external services and dependencies:
- Third-party APIs
- File system operations
- Email sending
- Time-dependent operations

```python
def test_email_service(mocker):
    mock_send = mocker.patch('services.email.send_mail')
    
    EmailService.send_welcome("user@test.com")
    
    mock_send.assert_called_with(
        to="user@test.com",
        subject="Welcome",
        body=mocker.ANY
    )
```

### When Not to Mock

Don't mock:
- Database operations (use test database)
- Model operations (use real models)
- Core business logic (test directly)

## Test Fixtures

### Database Fixtures

```python
# conftest.py
@pytest.fixture(scope="session")
def app():
    """Provides test Flask application"""
    from server.app import create_app  # This handles db.init_app()
    from server.config import TestingConfig
    
    # Configure test database
    test_config = TestingConfig()
    test_config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Create app and push context
    app = create_app(test_config)  # This calls db.init_app(app)
    app.config['TESTING'] = True
    
    ctx = app.app_context()
    ctx.push()
    
    # Create tables (db is already initialized)
    db.create_all()
    
    yield app
    
    # Cleanup
    db.session.remove()
    db.drop_all()
    ctx.pop()

@pytest.fixture(scope="function")
def db_session(app):
    """Provides database session"""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.session
    session.begin_nested()
    
    yield session
    
    session.rollback()
    transaction.rollback()
    connection.close()
```

Common SQLAlchemy Errors:

1. **"SQLAlchemy instance already registered"**
   ```
   RuntimeError: A 'SQLAlchemy' instance has already been registered on this Flask app
   ```
   - Cause: Calling db.init_app() multiple times
   - Solution: Let create_app() handle initialization
   - Don't call db.init_app() in test fixtures

2. **"Flask app not registered with SQLAlchemy instance"**
   ```
   RuntimeError: The current Flask app is not registered with this 'SQLAlchemy' instance
   ```
   - Cause: Using db outside app context or before initialization
   - Solution: Use app fixture and its context
   - Let create_app() handle db initialization

### Helper Fixtures

```python
@pytest.fixture
def auth_headers():
    """Provides authentication headers"""
    token = create_test_token()
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def test_user(db_session):
    """Provides test user"""
    user = User(name="Test User")
    db_session.add(user)
    db_session.commit()
    return user
```

## Best Practices

1. **One Concept Per Test**
   ```python
   # Good
   def test_user_validation():
       """Test user validation rules"""
   
   # Bad
   def test_user():  # Too broad
       """Test user creation, validation, and deletion"""
   ```

2. **Clear Test Names**
   ```python
   # Good
   def test_invalid_email_returns_400()
   
   # Bad
   def test_email()  # Too vague
   ```

3. **Descriptive Assertions**
   ```python
   # Good
   assert user.is_active is True, "New users should be active"
   
   # Bad
   assert user.is_active  # No context if fails
   ```

4. **Proper Setup and Cleanup**
   ```python
   # Good
   def test_file_upload(tmp_path):
       path = tmp_path / "test.txt"
       # Test using temporary path
   
   # Bad
   def test_file_upload():
       path = "test.txt"  # Creates file in working directory
   ```

## Running Tests

### Basic Commands

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/api/test_users.py

# Run specific test
python -m pytest tests/api/test_users.py::test_create_user
```

### Useful Options

```bash
# Show print statements
pytest -s

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show locals on failure
pytest -l

# Coverage report
pytest --cov=server
```

## Troubleshooting

### Common Issues

1. **Database Errors**
   - Check database configuration
   - Verify fixtures are used correctly
   - Ensure proper cleanup

2. **Import Errors**
   - Check import paths
   - Verify PYTHONPATH
   - Check for circular imports

3. **Fixture Errors**
   - Check fixture dependencies
   - Verify scope is appropriate
   - Check for proper cleanup

### Debug Tips

1. Use pytest -s to see print statements
2. Use pytest -v for verbose output
3. Use pytest --pdb to debug on failures
4. Check logs for detailed error messages
