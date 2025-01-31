# Server Architecture Guide

## Project Structure

```
server/
├── api/          # API endpoints and route handlers
├── core/         # Core business logic
├── models/       # Database models
├── services/     # Service layer between API and core
├── extensions/   # Flask extensions (db, etc.)
└── tests/        # Test suite
```

## Import Guidelines

### Consistent Import Pattern

All code should use imports relative to the server root:

```python
# CORRECT - Use these patterns
from extensions import db
from models import User, Batch
from models.niche import Niche
from services.batch_manager import BatchManager

# INCORRECT - Never use these patterns
from server.extensions import db  # Wrong: server prefix not needed
from .models import User  # Wrong: relative import
from ..services import BatchManager  # Wrong: relative import
```

This works because:
1. app.py adds server/ to PYTHONPATH:
   ```python
   server_dir = Path(__file__).resolve().parent
   if str(server_dir) not in sys.path:
       sys.path.insert(0, str(server_dir))
   ```

2. All imports are relative to server/:
   - extensions/ is directly under server/
   - models/ is directly under server/
   - services/ is directly under server/

3. Benefits:
   - Consistent pattern everywhere
   - No confusion about import styles
   - No circular dependencies
   - Easy to understand

## Database Configuration

### Model Definition

Models should be defined with clear table configuration:

```python
class User(BaseModel):
    __tablename__ = 'users'
    
    # For models with only options
    __table_args__ = {'extend_existing': True}
    
    # For models with constraints
    __table_args__ = (
        UniqueConstraint('email', name='uq_user_email'),
        {'extend_existing': True}
    )
```

The extend_existing=True option:
- Allows SQLAlchemy to update existing table definitions
- Prevents errors when tables are created multiple times
- Required for test database setup

### Database Initialization

The database is initialized in two places:

1. Application (app.py):
```python
def create_app():
    app = Flask(__name__)
    db.init_app(app)
    return app
```

2. Tests (conftest.py):
```python
@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig())
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
```

## Testing Strategy

### Database Tests

For tests requiring database access:

1. Use the @pytest.mark.real_db marker
2. Use the session-scoped app fixture
3. Let the fixture manage the database lifecycle

```python
@pytest.mark.real_db
def test_user_creation(app, db_session):
    user = User(name="Test")
    db_session.add(user)
    db_session.commit()
    assert User.query.count() == 1
```

Do NOT:
- Create additional app contexts
- Initialize database connections manually
- Mix real and mock database access

### Mock Tests

For tests not requiring database access:

1. Use the provided mock fixtures
2. Mock at the appropriate layer
3. Test one concept at a time

```python
def test_user_validation(client):
    response = client.post('/api/users', json={})
    assert response.status_code == 400
    assert 'name is required' in response.get_json()['error']
```

## Common Issues

### Table Already Defined

If you see "Table Already Defined" errors:

1. Check model definition:
   - Ensure __table_args__ includes extend_existing=True
   - Verify table name is unique
   - Check for duplicate model imports

2. Check test setup:
   - Use the provided app fixture
   - Don't create additional app contexts
   - Let fixtures manage database lifecycle

### Import Errors

If you see import errors:

1. In application code:
   - Use relative imports
   - Import from the current directory
   - Follow the established pattern in existing files

2. In test code:
   - Use server-prefixed absolute imports
   - Import only what's needed
   - Follow the examples in testing.md

### Database Connection

If you see database connection errors:

1. Check configuration:
   - Verify database URL is correct
   - Ensure environment variables are set
   - Check for typos in config

2. Check initialization:
   - Verify db.init_app is called
   - Ensure app context is active
   - Check connection string format