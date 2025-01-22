# Internal API Documentation

## Overview

The internal API is structured around four main resources:
- Niches (categories for organizing profiles)
- Profiles (Instagram user accounts)
- Batches (story checking jobs)
- Settings (system configuration)

All endpoints follow RESTful conventions and are prefixed with `/api`.

## Documentation Structure

- [Niche API](docs/api/niche.md) - Profile categorization endpoints
- [Profile API](docs/api/profile.md) - Instagram profile management
- [Batch API](docs/api/batch.md) - Story checking job management
- [Settings API](docs/api/settings.md) - System configuration
- [Development Guide](docs/development.md) - Setup and development workflow
- [Testing Guide](docs/testing.md) - Testing procedures and guidelines

## API Structure

### URL Patterns
- All routes are registered with `/api/{resource}` prefix
- Routes are defined without resource names in individual files
- Consistent patterns for CRUD operations

### Response Format
All responses are JSON formatted and include:
- Success responses: Relevant data or confirmation message
- Error responses: Error message and appropriate HTTP status code

### Common Status Codes
- 200: Success
- 201: Created
- 204: No Content (successful deletion)
- 400: Bad Request
- 404: Not Found
- 207: Multi-Status (for bulk operations)

## Implementation Details

### Route Registration
- Routes are defined in individual API files (niche.py, profile.py, etc.)
- Blueprints are registered in app.py with proper URL prefixes
- Each API module follows the same pattern for consistency

#### Blueprint Structure
```python
# In api/niche.py (and other API files)
niche_bp = Blueprint('niche', __name__)

@niche_bp.route('', methods=['GET'])  # Maps to /api/niches
@niche_bp.route('/<id>', methods=['GET'])  # Maps to /api/niches/{id}
```

```python
# In app.py
app.register_blueprint(niche_bp, url_prefix='/api/niches')
app.register_blueprint(profile_bp, url_prefix='/api/profiles')
app.register_blueprint(batch_bp, url_prefix='/api/batches')
app.register_blueprint(settings_bp, url_prefix='/api/settings')
```

#### Important Route Patterns
1. Root routes use empty string ('') not '/'
2. No resource name in routes (e.g., '' not '/niches')
3. Sub-resource routes start with '/' (e.g., '/reorder')
4. URL prefixes handle the full path structure

## Common Patterns

### Error Handling
```python
try:
    db.session.add(model)
    db.session.commit()
except IntegrityError as e:
    db.session.rollback()
    # Handle specific database constraints
except Exception as e:
    db.session.rollback()
    # Handle unexpected errors
```

### Status Management
- Consistent status transitions
- Status-based filtering
- Status validation

### Rate Limiting
- Configurable via settings
- Per-proxy limits
- Global rate limits

### Auto-Cleanup
- Automatic cleanup of old data
- Configurable retention periods
- Background cleanup tasks
