# Worker Manager

The worker manager provides a thread-safe pool of workers for checking Instagram stories. It handles proxy rotation, rate limiting, and resource management.

## Design Overview

### Components

1. **Worker Pool**
   - Initializes on-demand when starting batches
   - Manages a collection of workers
   - Enforces concurrent worker limits
   - Tracks proxy and session states
   - Implements least-recently-used proxy selection
   - Cleans up resources automatically

2. **Individual Workers**
   - Handle story checking for profiles
   - Track rate limits and errors
   - Manage proxy-session pairs
   - Auto-disable on repeated failures

### Key Features

1. **Rate Limit Handling**
   ```python
   # Hourly limits per proxy
   if requests_this_hour >= hourly_limit:
       worker.is_rate_limited = True  # Use rate_limited flag
       proxy.rate_limited = True      # Update database state
       proxy.last_used = datetime.now(UTC)  # Track usage time
   ```
   - Per-proxy request counting
   - Automatic cooldown periods
   - Rate limit detection and recovery
   - Pool state synchronization

2. **Proxy Rotation**
   ```python
   # Get least recently used proxy
   available_proxies.sort(key=lambda p: last_used.get(p, datetime.min))
   next_proxy = available_proxies[0]
   ```
   - Least-recently-used selection
   - Automatic proxy rotation on failures
   - State-aware proxy filtering
   - Proxy health tracking

3. **Resource Management**
   ```python
   def release_worker(self, worker):
       # Remove from active pool
       self.active_workers.remove(worker)
       # Update states
       self.last_used[worker.proxy] = datetime.now()
       # Add back if healthy
       if not worker.is_disabled and not worker.is_rate_limited:
           self.available_workers.append(worker)
   ```
   - Automatic resource cleanup
   - Session tracking and reuse
   - Worker state management
   - Pool cleanup on shutdown

4. **Error Handling**
   ```python
   # Disable worker after max errors
   if error_count >= max_errors:
       worker.is_disabled = True
       pool.remove_worker(worker)
   ```
   - Error thresholds with auto-disable
   - Rate limit detection
   - Connection error handling
   - State recovery mechanisms

## Usage Examples

### Creating Workers
```python
# Initialize pool
pool = WorkerPool()

# Add proxy-session pair
pool.add_proxy_session(
    proxy="http://proxy:8080",
    session_cookie="session_id=abc123"
)
```

### Checking Stories
```python
# Get available worker
worker = pool.get_worker()
if worker:
    try:
        success = await worker.check_story(batch_profile)
        if success:
            # Story check completed
    finally:
        pool.release_worker(worker)
```

### Rate Limit Recovery
```python
# Clear rate limit after cooldown
worker.clear_rate_limit()
worker.requests_this_hour = 0
worker.hour_start = datetime.now()
```

## Configuration

### System Settings
```python
class SystemSettings:
    max_threads = 3          # Max concurrent workers
    proxy_max_failures = 3   # Error threshold
    proxy_hourly_limit = 50  # Requests per hour
```

### Pool States
```python
proxy_states = {
    'proxy_url': {
        'disabled': False,    # Error threshold exceeded
        'rate_limited': False # Hourly limit reached
    }
}
```

## Implementation Details

### Thread Safety
- Worker pool operations are thread-safe
- State updates use atomic operations
- Resource cleanup handles race conditions

### State Management
1. Worker States
   - Active: Currently processing
   - Available: Ready for use
   - Disabled: Not active (is_active = False)
   - Rate Limited: Hourly limit reached (rate_limited = True)

2. Proxy States
   - Tracks disabled/rate-limited status
   - Maintains last used timestamps
   - Records error counts

### Resource Lifecycle
1. Initialization
   - Initialize worker pool on-demand when starting batches
   - Load active proxies and valid sessions
   - Initialize states
   - Track proxy usage times

2. Operation
   - Get worker from pool
   - Process stories
   - Handle errors/limits
   - Release worker

3. Cleanup
   - Remove disabled workers
   - Clear rate limits
   - Release resources

## Testing

Comprehensive test suite covers:
1. Proxy validation and reuse
2. Rate limit handling
3. Error thresholds
4. Resource cleanup
5. Concurrent operations

```python
# Example test
async def test_rate_limit():
    worker = pool.get_worker()
    for _ in range(hourly_limit):
        await worker.check_story(profile)
    assert worker.is_rate_limited
```

## Integration with Story Checker

### Story Checking Flow
```python
class Worker:
    async def check_story(self, batch_profile):
        # Validate session first
        if not self.proxy_session.session.is_valid():
            return False
            
        # Initialize story checker
        self.story_checker = StoryChecker(self.proxy_session)
        
        try:
            # Check rate limits
            if self.is_rate_limited:
                return False
                
            # Perform check
            has_story = await self.story_checker.check_profile(username)
            self.requests_this_hour += 1
            return True
            
        except Exception as e:
            if "Rate limited" in str(e):
                self.is_rate_limited = True
```

1. **Rate Limiting**
   - Browser-like rate limiting
   - Per-proxy request tracking
   - Minimum delays between requests
   - Hourly and per-minute limits

2. **Session Management**
   - Just-in-time session creation
   - Automatic cleanup
   - Session cookie handling
   - Connection pooling

3. **Error Handling**
   - Rate limit detection
   - Network error recovery
   - Response validation
   - Session refresh

## Integration with Batch Processing and Queue Management

### Batch Processing Flow
```python
async def process_batch(batch_id: str, worker_pool: WorkerPool):
    # Get available worker
    worker = worker_pool.get_worker()
    if worker:
        try:
            # Check story
            success = await worker.check_story(batch_profile)
            if success:
                batch.checked_profiles += 1
        finally:
            worker_pool.release_worker(worker)
    
    # After batch completion
    QueueManager.mark_completed(batch_id)
    QueueManager.promote_next_batch()
```

1. **Worker Assignment**
   - Workers are assigned per profile check
   - Automatic retry with different workers on rate limits
   - Maximum 3 retry attempts per profile

2. **State Management**
   - Batch tracks overall progress
   - Individual profile status updates
   - Worker health monitoring during batch

3. **Error Recovery**
   - Rate limit detection and retry
   - Failed checks tracking
   - Batch status preservation

4. **Queue Management**
   - Automatic batch completion marking
   - Promotion of next batch in queue
   - Continuous processing of queued batches

### Interaction with Queue Manager

The Worker Manager now interacts closely with the Queue Manager to ensure smooth and continuous processing of batches:

1. **Batch Completion**
   - When a batch is completed, the Worker Manager signals the Queue Manager
   - The Queue Manager marks the batch as completed and updates its status

2. **Next Batch Promotion**
   - After marking a batch as completed, the Queue Manager automatically promotes the next batch in the queue
   - The Worker Manager is then responsible for starting the processing of the newly promoted batch

3. **Continuous Processing**
   - This cycle of completion and promotion ensures that batches are processed continuously without manual intervention
   - The Worker Manager always has a batch to process as long as there are batches in the queue

4. **Resource Optimization**
   - The Worker Manager can now optimize resource usage based on the queue state
   - For example, it can adjust the number of active workers based on the number of queued batches

## Best Practices

1. Resource Management
   - Always release workers after use
   - Clean up resources on shutdown
   - Monitor proxy health

2. Error Handling
   - Handle rate limits gracefully
   - Implement retry mechanisms
   - Log errors for debugging

3. Configuration
   - Tune settings for workload
   - Monitor resource usage
   - Adjust limits as needed

4. Batch Processing
   - Monitor batch progress
   - Track worker health
   - Handle partial failures
