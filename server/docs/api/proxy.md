# Proxy Management System

The proxy management system provides functionality for managing and rotating proxies with their associated Instagram sessions. This document outlines the key components and APIs.

## Models

### Proxy Model
- Represents a proxy server with connection details and performance metrics
- Fields:
  - `ip`: Proxy IP address (required)
  - `port`: Proxy port number (required)
  - `username`: Authentication username (optional)
  - `password`: Authentication password (optional)
  - `is_active`: Whether proxy is enabled
  - `total_requests`: Total number of requests made
  - `failed_requests`: Number of failed requests
  - `requests_this_hour`: Request count for current hour
  - `error_count`: Consecutive error count
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

### Session Model
- Represents an Instagram session associated with a proxy
- Fields:
  - `proxy_id`: Associated proxy ID (required)
  - `session`: Instagram session cookie (required, unique)
  - `status`: Session status (active/disabled)
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

## API Endpoints

### List Proxies
```
GET /api/proxies
```
Returns list of all proxies with their associated sessions.

Response:
```json
[
  {
    "id": 1,
    "ip": "192.168.1.1",
    "port": 8080,
    "username": "user",
    "password": "pass",
    "is_active": true,
    "total_requests": 100,
    "failed_requests": 5,
    "requests_this_hour": 20,
    "error_count": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T01:00:00Z",
    "sessions": [
      {
        "id": 1,
        "session": "session_cookie",
        "status": "active"
      }
    ]
  }
]
```

### Create Proxy
```
POST /api/proxies
```
Create new proxy with associated session.

Request Body:
```json
{
  "ip": "192.168.1.1",
  "port": 8080,
  "username": "user", // optional
  "password": "pass", // optional
  "session": "session_cookie"
}
```

Response (201 Created):
```json
{
  "id": 1,
  "ip": "192.168.1.1",
  "port": 8080,
  "username": "user",
  "password": "pass",
  "is_active": true,
  "total_requests": 0,
  "failed_requests": 0,
  "requests_this_hour": 0,
  "error_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "sessions": [
    {
      "id": 1,
      "session": "session_cookie",
      "status": "active"
    }
  ]
}
```

### Delete Proxy
```
DELETE /api/proxies/{proxy_id}
```
Delete proxy and its associated sessions.

Response (204 No Content)

### Update Proxy Status
```
PATCH /api/proxies/{proxy_id}/status
```
Update proxy active status.

Request Body:
```json
{
  "status": "active" // or "disabled"
}
```

Response:
```json
{
  "id": 1,
  "ip": "192.168.1.1",
  "port": 8080,
  "username": "user",
  "password": "pass",
  "is_active": true,
  "total_requests": 100,
  "failed_requests": 5,
  "requests_this_hour": 20,
  "error_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T01:00:00Z"
}
```

## Error Handling

All endpoints return standardized error responses:

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
- `duplicate_proxy`: Proxy with same IP/port exists
- `duplicate_session`: Session cookie already in use
- `not_found`: Requested resource not found
- `database_error`: Database operation failed

## Frontend Store

The proxy management system includes a frontend store (proxyStore.js) that provides:

- Proxy CRUD operations
- Performance monitoring
- Health tracking
- Proxy rotation settings
- Status management

Key features:
- Automatic proxy rotation based on performance metrics
- Health history tracking with configurable window
- Request rate limiting per proxy
- Error threshold monitoring
- Performance metrics aggregation

## Testing

The system includes comprehensive tests:
- Model tests (test_proxy.py, test_session.py)
- API tests (test_proxy.py)
- Store tests (proxyStore.test.js)

Test coverage includes:
- Basic CRUD operations
- Validation rules
- Unique constraints
- Status transitions
- Performance tracking
- Error handling
- Session management
