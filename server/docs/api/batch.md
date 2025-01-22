# Batch API

Manages story checking batch jobs with just-in-time proxy assignment and rate limit handling.

## Data Structure

### Batch
```json
{
  "id": "string",
  "niche_id": "string",
  "status": "string",
  "total_profiles": number,
  "completed_profiles": number,
  "successful_checks": number,
  "failed_checks": number,
  "completion_rate": number,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### BatchProfile
```json
{
  "id": "string",
  "batch_id": "string",
  "profile_id": "string",
  "proxy_id": "string",
  "session_id": "string",
  "status": "string",
  "has_story": boolean,
  "processed_at": "datetime",
  "error": "string"
}
```

### Status Values
- queued: Initial state, ready for processing
- in_progress: Currently processing
- done: All profiles checked
- failed: Critical error during processing

## Endpoints

### List Batches
```http
GET /api/batches
```

List all batches.

#### Response (200 OK)
```json
[
  {
    "id": "string",
    "niche_id": "string",
    "status": "string",
    "total_profiles": number,
    "completed_profiles": number,
    "successful_checks": number,
    "failed_checks": number,
    "completion_rate": number,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

### Create Batch
```http
POST /api/batches
```

Create a new batch job.

#### Request Body
```json
{
  "niche_id": "string",
  "profile_ids": ["string"]
}
```

#### Response (201 Created)
```json
{
  "id": "string",
  ...batch data
}
```

#### Error Responses
- 400: niche_id is required
- 400: profile_ids must be a non-empty list
- 400: Invalid niche ID or profile IDs

### Start Batches
```http
POST /api/batches/start
```

Start processing selected batches. Only one batch can be processing at a time.

#### Request Body
```json
{
  "batch_ids": ["string"]
}
```

#### Response (200 OK)
```json
[
  {
    "id": "string",
    ...batch data with status="in_progress"
  }
]
```

#### Error Responses
- 400: batch_ids is required
- 404: No queued batches found with the provided IDs
- 409: Another batch is already running

### Stop Batches
```http
POST /api/batches/stop
```

Stop selected batches, returning them to queued state.

#### Request Body
```json
{
  "batch_ids": ["string"]
}
```

#### Response (200 OK)
```json
[
  {
    "id": "string",
    ...batch data with status="queued"
  }
]
```

#### Error Responses
- 400: batch_ids is required
- 404: No batches found with the provided IDs

### Delete Batches
```http
DELETE /api/batches
```

Delete selected batches and their associated profiles.

#### Request Body
```json
{
  "batch_ids": ["string"]
}
```

#### Response (204 No Content)

#### Error Responses
- 400: batch_ids is required
- 404: No batches found with the provided IDs

## Implementation Details

### Batch Processing Flow

1. Creation
   - Validate niche_id and profile_ids
   - Create batch in 'queued' state
   - Create batch_profile records for each profile

2. Starting
   - Check for running batches (only one allowed)
   - Move batch from 'queued' to 'in_progress'
   - Begin processing profiles

3. Processing
   - Get available proxy from pool
   - Check story with proxy
   - Handle rate limits with retries
   - Update profile and batch stats
   - Release proxy back to pool

4. Completion
   - All profiles processed
   - Update final stats
   - Move to 'done' state

### Concurrency Control and Queue Management

1. Single Batch Processing
   - Only one batch can be in 'in_progress' state at a time
   - Attempts to start additional batches will result in a 409 Conflict response

2. Improved Queuing System
   - Batches are processed in the order they are started
   - Subsequent batches remain in 'queued' state until the current batch is completed or stopped
   - Automatic promotion of the next batch in the queue when the current batch completes
   - Continuous processing of batches without manual intervention

3. Queue Reordering
   - After a batch completes or is removed from the queue, the remaining batches are automatically reordered
   - This ensures that queue positions remain sequential and optimized

4. Automatic Batch Promotion
   - When a batch completes processing, the system automatically promotes the next batch in the queue to the 'in_progress' state
   - This process continues as long as there are batches in the queue, ensuring continuous processing

### Rate Limit Handling

1. Detection
   - Identify rate limit responses
   - Mark proxy as rate limited
   - Set cooldown period

2. Retry Logic
   - Retry with different proxy
   - Up to 3 retry attempts per profile
   - Clear errors after successful retry

3. Cooldown
   - Based on system settings
   - Proxy-specific cooldown periods
   - Automatic proxy rotation

### Resource Management

1. Proxy Management
   - Dynamic proxy assignment
   - Health tracking
   - Automatic cooldown and rotation

2. Session Handling
   - Just-in-time session creation
   - Session tracking for cleanup
   - Automatic session closure

3. Cleanup
   - Resource release after batch completion
   - Error state cleanup

### Error Handling

1. Rate Limits
   - Automatic retry with new proxy
   - Error cleared after success
   - Batch continues processing other profiles

2. Network Errors
   - Retry non-rate-limit errors
   - Error details preserved in BatchProfile
   - Batch continues with next profile after max retries

3. Validation
   - Input validation for all API endpoints
   - State transition validation
   - Resource availability checks

### Usage Examples

#### Creating a Batch
```python
response = requests.post('/api/batches', json={
    'niche_id': 'fashion_niche_id',
    'profile_ids': ['profile1', 'profile2']
})
batch = response.json()
```

#### Starting a Batch
```python
response = requests.post('/api/batches/start', json={
    'batch_ids': [batch['id']]
})
if response.status_code == 409:
    print("Another batch is already running")
```

#### Monitoring Progress
```python
response = requests.get('/api/batches')
batches = response.json()
for batch in batches:
    print(f"Batch {batch['id']}: {batch['completion_rate']}% complete")
```

### Best Practices

1. Batch Creation
   - Group related profiles
   - Use reasonable batch sizes (e.g., 100-1000 profiles)
   - Validate inputs before submission

2. Processing
   - Start one batch at a time
   - Monitor completion rate and errors
   - Be prepared to handle 409 Conflict responses

3. Error Handling
   - Implement client-side retry logic for network issues
   - Check individual profile statuses for detailed error information
   - Use exponential backoff for retries

4. Resource Management
   - Regularly check and maintain proxy health
   - Implement proper error handling and resource cleanup in client applications

5. Monitoring
   - Regularly poll batch status for long-running batches
   - Implement logging and alerting for batch processing issues

## Batch Log Feature

The Batch Log feature provides detailed, real-time logging information for each batch processing operation. This feature allows users to view granular information about the progress and status of individual profile checks within a batch.

### Batch Log Data Structure

```json
{
  "id": "string",
  "batch_id": "string",
  "timestamp": "datetime",
  "event_type": "string",
  "message": "string",
  "profile_id": "string",
  "proxy_id": "string"
}
```

### Event Types

- BATCH_QUEUED: Batch has been created and queued for processing
- BATCH_START: Batch processing started
- BATCH_PAUSE: Batch processing paused (if pause functionality is implemented)
- BATCH_RESUME: Batch processing resumed after a pause
- PROFILE_CHECK_START: Started checking a profile for story
- PROFILE_CHECK_END: Finished checking a profile for story
- STORY_FOUND: A story was found for a profile
- STORY_NOT_FOUND: No story was found for a profile
- PROXY_ASSIGNED: A proxy was assigned to a profile check
- PROXY_RELEASED: A proxy was released after a profile check
- PROXY_RATE_LIMITED: A proxy hit a rate limit
- PROXY_ERROR: An error occurred with a proxy
- RETRY_ATTEMPT: A retry was attempted for a profile check
- MAX_RETRIES_REACHED: Maximum number of retries reached for a profile
- PROFILE_ERROR: An error occurred while processing a specific profile
- BATCH_PROGRESS_UPDATE: Periodic update on batch progress (e.g., every 10% completion)
- BATCH_HALF_COMPLETE: Batch is 50% complete
- BATCH_ALMOST_COMPLETE: Batch is 90% complete
- BATCH_END: Batch processing completed
- BATCH_CANCELLED: Batch processing was cancelled by the user
- DATABASE_UPDATE: A database update was performed (e.g., updating profile stats)
- WORKER_ASSIGNED: A worker was assigned to process part of the batch
- WORKER_RELEASED: A worker finished its assigned work
- RESOURCE_LIMIT_REACHED: A resource limit was reached (e.g., memory, CPU)
- SYSTEM_ERROR: A system-level error occurred during processing
- UNEXPECTED_ERROR: An unexpected error occurred that doesn't fit other categories
- CONFIG_CHANGE: A configuration change was made during batch processing
- EXTERNAL_API_CALL: An external API was called (if applicable)
- EXTERNAL_API_RESPONSE: Response received from an external API call
- BATCH_STATS_UPDATE: Batch statistics were updated

### Endpoints

#### Get Batch Logs

```http
GET /api/batches/{batch_id}/logs
```

Retrieve logs for a specific batch.

##### Query Parameters
- start_time: ISO 8601 datetime string (optional)
- end_time: ISO 8601 datetime string (optional)
- limit: number (optional, default 100)
- offset: number (optional, default 0)

##### Response (200 OK)
```json
{
  "logs": [
    {
      "id": "string",
      "batch_id": "string",
      "timestamp": "datetime",
      "event_type": "string",
      "message": "string",
      "profile_id": "string",
      "proxy_id": "string"
    }
  ],
  "total": number,
  "limit": number,
  "offset": number
}
```

### Implementation Details

1. Logging Mechanism
   - Implement a new BatchLog model in the database
   - Create a logging service to handle log creation and storage
   - Integrate logging calls throughout the batch processing flow

2. API Integration
   - Add a new endpoint to retrieve batch logs
   - Implement filtering and pagination for log retrieval

3. Front-end Integration
   - Add a "View Logs" button to each batch row in the BatchTable component
   - Create a BatchLogModal component to display logs in a popup
   - Implement real-time log updates using WebSocket or polling

### Best Practices for Batch Logging

1. Performance Considerations
   - Use bulk inserts for log entries to minimize database operations
   - Implement log rotation or archiving for older logs to manage database size

2. Security
   - Ensure that sensitive information (e.g., full proxy URLs) is not logged
   - Implement access control to restrict log viewing to authorized users

3. User Experience
   - Provide clear, human-readable log messages
   - Implement filtering and search functionality in the log viewer

4. Monitoring and Alerting
   - Use log data to generate alerts for critical events or errors
   - Implement log analysis for performance monitoring and optimization
