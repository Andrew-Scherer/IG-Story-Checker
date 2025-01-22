# API Documentation

The API uses a hierarchical blueprint structure for organizing routes and features.

## Route Structure

```
/api                    # Main API prefix (api_bp)
  /niches              # Niche routes (niche_bp) 
    GET /              # List niches
    POST /             # Create niche
    GET /<id>          # Get niche
    PUT /<id>          # Update niche
    DELETE /<id>       # Delete niche
    
  /profiles            # Profile routes (profile_bp)
    GET /              # List profiles
    POST /             # Create profile
    GET /<id>          # Get profile
    PUT /<id>          # Update profile
    DELETE /<id>       # Delete profile
    
  /batches             # Batch routes (batch_bp)
    GET /              # List batches
    POST /             # Create batch
    GET /<id>          # Get batch
    PUT /<id>          # Update batch
    DELETE /<id>       # Delete batch
    
  /settings            # Settings routes (settings_bp)
    GET /              # Get settings
    PUT /              # Update settings
    
  /proxies             # Proxy routes (proxy_bp)
    GET /              # List proxies
    POST /             # Create proxy
    DELETE /<id>       # Delete proxy
    PATCH /<id>/status # Update proxy status
```

## Blueprint Registration

The blueprints are registered in `__init__.py` with the following structure:

1. Main `api_bp` blueprint with `/api` prefix
2. Feature blueprints registered to `api_bp` with their respective prefixes:
   - `/niches` for niche_bp
   - `/profiles` for profile_bp
   - `/batches` for batch_bp
   - `/settings` for settings_bp
   - `/proxies` for proxy_bp

## Detailed Documentation

Each API section has detailed documentation covering models, endpoints, request/response formats, and error handling:

- [Batch Processing](docs/api/batch.md)
- [Niche Management](docs/api/niche.md)
- [Profile Management](docs/api/profile.md)
- [Proxy Management](docs/api/proxy.md)

## Common Features

All API endpoints share these common features:

### Error Handling
All errors follow a standard format:
```json
{
  "error": "error_type",
  "message": "Human readable message",
  "details": {
    // Additional error details
  }
}
```

Common error types:
- `validation_error`: Missing or invalid fields
- `invalid_request`: Invalid request format/data
- `not_found`: Requested resource not found
- `database_error`: Database operation failed

### Authentication
- All endpoints require authentication (except health check)
- Use Bearer token in Authorization header
- Token expiration and refresh handled by auth middleware

### Request/Response Format
- All requests with body must use JSON
- All responses are JSON formatted
- Use standard HTTP status codes
- Include pagination for list endpoints
- Support filtering and sorting where applicable

DO NOT MODIFY THIS STRUCTURE as it will break the frontend API calls.
