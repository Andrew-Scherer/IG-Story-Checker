# Settings API

Manages system-wide configuration settings. Handles rate limits, batch processing parameters, and notification settings.

## Data Structure

```json
{
  "profiles_per_minute": number,
  "max_threads": number,
  "default_batch_size": number,
  "story_retention_hours": number,
  "auto_trigger_enabled": boolean,
  "min_trigger_interval": number,
  "proxy_test_timeout": number,
  "proxy_max_failures": number,
  "proxy_hourly_limit": number,
  "notifications_enabled": boolean,
  "notification_email": "string"
}
```

## Settings Description

### Rate Limiting
- profiles_per_minute: Maximum profiles to check per minute
- proxy_hourly_limit: Maximum requests per hour per proxy
- min_trigger_interval: Minutes between auto-triggered batches

### Batch Processing
- max_threads: Maximum concurrent processing threads
- default_batch_size: Default number of profiles per batch
- story_retention_hours: How long to keep story results

### Proxy Management
- proxy_test_timeout: Seconds to wait for proxy test
- proxy_max_failures: Failures before disabling proxy

### Notifications
- notifications_enabled: Enable email notifications
- notification_email: Address for system notifications

## Endpoints

### Get Settings
```http
GET /api/settings
```

Get current system settings.

#### Response
```json
{
  "profiles_per_minute": number,
  "max_threads": number,
  "default_batch_size": number,
  "story_retention_hours": number,
  "auto_trigger_enabled": boolean,
  "min_trigger_interval": number,
  "proxy_test_timeout": number,
  "proxy_max_failures": number,
  "proxy_hourly_limit": number,
  "notifications_enabled": boolean,
  "notification_email": "string"
}
```

### Update Settings
```http
PUT /api/settings
```

Update system settings.

#### Request Body
Any subset of settings fields:
```json
{
  "profiles_per_minute": number,
  "max_threads": number,
  "default_batch_size": number,
  ...
}
```

#### Response
```json
{
  ...updated settings
}
```

#### Error Responses
- 400: Validation errors (with details)

## Implementation Notes

### Model Details
The SystemSettings model:
- Singleton pattern (single settings record)
- Default values for all settings
- Validation for numeric ranges
- Email format validation

### Key Features

1. Rate Limiting
   - Global rate limits for profile checking
   - Per-proxy rate limiting
   - Configurable intervals

2. Resource Management
   - Thread pool configuration
   - Batch size optimization
   - Data retention policies

3. Proxy Configuration
   - Timeout settings
   - Failure thresholds
   - Usage limits

4. Notification System
   - Email notifications
   - Configurable triggers
   - Format validation

### Validation Rules

#### Numeric Fields
- profiles_per_minute: > 0
- max_threads: > 0
- default_batch_size: > 0, <= 10000
- story_retention_hours: > 0
- min_trigger_interval: > 0
- proxy_test_timeout: > 0
- proxy_max_failures: > 0
- proxy_hourly_limit: > 0

#### Email Validation
- RFC 5322 compliant
- Required if notifications enabled
- DNS validation optional

### Usage Examples

#### Updating Rate Limits
```python
response = requests.put('/api/settings', json={
    'profiles_per_minute': 50,
    'proxy_hourly_limit': 200
})
```

#### Configuring Notifications
```python
response = requests.put('/api/settings', json={
    'notifications_enabled': True,
    'notification_email': 'admin@example.com'
})
```

#### Optimizing Resources
```python
response = requests.put('/api/settings', json={
    'max_threads': 5,
    'default_batch_size': 200
})
```

### Impact on Other Systems

1. Batch Processing
   - Rate limits affect processing speed
   - Thread count impacts concurrency
   - Batch size affects memory usage

2. Proxy Management
   - Timeout affects reliability detection
   - Failure threshold affects availability
   - Rate limits affect proxy rotation

3. Data Management
   - Retention period affects database size
   - Batch size affects query performance
   - Thread count affects database connections

4. Monitoring
   - Email notifications for system events
   - Rate limit violations
   - Proxy health status
