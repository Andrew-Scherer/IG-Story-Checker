# Development Guide

## Environment Setup

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Node.js 18+ (for client)
- Redis (optional, for caching)

### Initial Setup

1. Clone Repository
```bash
git clone <repository-url>
cd ig-story-checker
```

2. Create Python Environment
```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Database Setup
```bash
# Create development database
createdb ig_story_checker_dev

# Create test database
createdb ig_story_checker_test

# Run migrations
flask db upgrade
```

4. Environment Configuration
Create `.env` file in server directory:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ig_story_checker_dev
POSTGRES_TEST_DB=ig_story_checker_test

FLASK_APP=app.py
FLASK_ENV=development
```

## Project Structure

```
server/
├── api/                 # API endpoints
│   ├── niche.py        # Niche management
│   ├── profile.py      # Profile management
│   ├── batch.py        # Batch processing
│   └── settings.py     # System settings
├── models/             # Database models
├── core/              # Core business logic
├── migrations/        # Database migrations
├── tests/            # Test suites
└── docs/             # Documentation
```

## Development Workflow

### Running the Server
```bash
# Start development server
flask run

# With debugger and auto-reload
FLASK_DEBUG=1 flask run
```

### Database Management

#### Creating Migrations
```bash
# After model changes
flask db migrate -m "description"

# Review migration file in migrations/versions/
# Apply migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

#### Adding Columns
For quick column additions without migrations, use scripts:
```python
# Example: add_proxy_columns.py
def add_columns():
    """Add new columns to existing table"""
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    
    # Add column if it doesn't exist
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'table_name' 
            AND column_name = 'column_name'
        ) THEN
            ALTER TABLE table_name ADD COLUMN column_name COLUMN_TYPE;
        END IF;
    END
    $$;
    """)
    conn.commit()
```

#### Database Reset
```bash
# Drop and recreate database
dropdb ig_story_checker_dev
createdb ig_story_checker_dev
flask db upgrade
```

### Code Style

#### Python
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for classes and functions

Example:
```python
from typing import Optional, List

def get_active_profiles(niche_id: Optional[str] = None) -> List[Profile]:
    """Get active profiles, optionally filtered by niche.
    
    Args:
        niche_id: Optional niche ID to filter by
        
    Returns:
        List of active Profile instances
    """
    query = Profile.query.filter_by(status='active')
    if niche_id:
        query = query.filter_by(niche_id=niche_id)
    return query.all()
```

### API Development

#### Adding New Endpoints

1. Create Route
```python
@blueprint.route('/path', methods=['GET'])
def handler():
    """Endpoint description"""
    # Implementation
    return jsonify(result)
```

2. Add Tests
```python
def test_endpoint(client):
    """Test description"""
    response = client.get('/api/path')
    assert response.status_code == 200
    # Additional assertions
```

3. Update Documentation
- Add endpoint to appropriate API doc
- Include request/response examples
- Document error cases

#### Modifying Existing Endpoints

1. Review Existing Tests
2. Make Changes
3. Update Tests
4. Update Documentation
5. Test Backwards Compatibility

### Error Handling

#### Standard Error Response
```python
def error_response(message: str, status_code: int = 400) -> tuple:
    return jsonify({'error': message}), status_code
```

#### Common Error Patterns
```python
# Not Found
if not item:
    return error_response('Item not found', 404)

# Validation Error
if not valid:
    return error_response('Invalid data', 400)

# Database Error
try:
    db.session.commit()
except IntegrityError:
    db.session.rollback()
    return error_response('Database constraint violation', 400)
```

## Common Tasks

### Adding a Model

1. Create Model Class
```python
class NewModel(BaseModel):
    """Model description"""
    __tablename__ = 'table_name'
    
    id = Column(String(36), primary_key=True)
    # Add fields
```

2. Create Migration
```bash
flask db migrate -m "add new model"
```

3. Add Tests
```python
def test_new_model():
    """Test model creation and validation"""
    instance = NewModel(field='value')
    assert instance.field == 'value'
```

### Adding an API Feature

1. Plan the Feature
   - Define endpoints
   - Design data structures
   - Consider error cases

2. Implement Models
   - Add/modify model classes
   - Create migrations
   - Add model tests

3. Implement API
   - Add routes
   - Add validation
   - Add error handling

4. Add Tests
   - Unit tests
   - Integration tests
   - Edge cases

5. Update Documentation
   - API documentation
   - Usage examples
   - Error scenarios

## Troubleshooting

### Common Issues

1. Database Connection
```python
# Test connection
from sqlalchemy import create_engine, text
engine = create_engine(DATABASE_URL)
try:
    connection = engine.connect()
    # Always use text() for raw SQL
    connection.execute(text('SELECT 1'))
    # Connection successful
finally:
    connection.close()
```

2. Raw SQL Execution
```python
# Always use SQLAlchemy text() for raw SQL
from sqlalchemy import text
db.session.execute(text('SELECT 1'))

# Not this (will fail):
db.session.execute('SELECT 1')
```

2. Migration Issues
```bash
# Reset migrations
flask db stamp head
flask db migrate
flask db upgrade
```

3. Import Issues
```python
# Add to __init__.py
from .module import Class
# Use absolute imports
from app.models import Model
```

### Debugging Tips

1. SQLAlchemy Logging
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

2. Request Debugging
```python
@app.before_request
def log_request():
    app.logger.debug(f"Request: {request.method} {request.url}")
```

3. Response Debugging
```python
@app.after_request
def log_response(response):
    app.logger.debug(f"Response: {response.status_code}")
    return response
