# Batch Implementation Test Plan

## Core Workflow
1. Profile Selection
   - User selects profiles to check for stories
   - No proxy assignment at this stage

2. Batch Creation
   - Create batch record with selected profiles
   - Initial status: 'queued'
   - No proxy assignment at this stage

3. Batch Processing
   - When batch starts:
     a. Get available proxy-session pair from pool
     b. Verify proxy is responsive
     c. Use proxy for current profile check
     d. Release proxy back to pool
     e. Repeat for next profile
   - Track progress (checked_profiles, stories_found)
   - Update batch status (queued -> in_progress -> done)
   - Handle rate limits with automatic retries
   - Clean up sessions after use

4. Results
   - Update profile stats (active_story, last_story_detected, etc.)
   - Update batch completion stats
   - Clear any transient errors after successful retries

## Test Structure

### Phase 1: Setup Tests ✓
- [x] Create test fixtures
  - [x] Niche creation helper
  - [x] Profile creation helper
  - [x] Mock story checker helper
  - [x] Worker pool helper
- [x] Tests pass

### Phase 2: Model Tests (server/tests/models/test_batch.py) ✓
- [x] Basic batch creation
  - [x] Verify batch fields (id, niche_id, status, etc.)
  - [x] Verify initial queued state
- [x] Status transitions (queued -> in_progress -> done)
- [x] Record check updates (checked_profiles, stories_found, completion_rate)
- [x] Tests pass

### Phase 3: API Tests (server/tests/api/test_batch.py) ✓
- [x] Create batch endpoint
  - [x] Success case with valid profiles
  - [x] Error case with invalid data
- [x] Start batch endpoint
  - [x] Success case for queued batch
  - [x] Error case for invalid batch
  - [x] Prevent concurrent batch processing (409 response)
- [x] List batches endpoint
  - [x] Verify batch listing with stats
- [x] Tests pass

### Phase 4: Worker Tests (server/tests/core/test_worker_manager.py) ✓
- [x] Proxy Management
  - [x] Get available proxy from pool
  - [x] Verify proxy before use
  - [x] Handle proxy validation failures
  - [x] Release proxy after use
- [x] Rate Limiting
  - [x] Handle rate limit detection
  - [x] Cooldown period management
  - [x] Retry with different proxy
- [x] Tests pass

### Phase 5: Batch Processor Tests (server/tests/core/test_batch_processor.py) ✓
- [x] Processing Flow
  - [x] Get worker for each profile
  - [x] Process profiles sequentially
  - [x] Handle worker unavailability
  - [x] Update batch progress
- [x] Error Handling
  - [x] Handle profile check failures
  - [x] Handle proxy validation failures
  - [x] Handle rate limits with retries
  - [x] Clear errors after successful retries
- [x] Tests pass

### Phase 6: Integration Tests (server/tests/integration/test_batch_workflow.py) ✓
- [x] Complete Workflow
  1. Create batch with profiles
  2. Start processing
  3. Verify just-in-time proxy assignment
  4. Verify results update correctly
- [x] Concurrent Processing
  - [x] Handle multiple batches
  - [x] Verify proxy reuse
  - [x] Verify proper queuing
  - [x] Verify 409 response for concurrent starts
- [x] Rate Limit Handling
  - [x] Retry with different proxy after rate limit
  - [x] Clear errors after successful retry
  - [x] Verify batch completion after retries
- [x] Resource Management
  - [x] Track and cleanup sessions
  - [x] Prevent session leaks
  - [x] Proper proxy release
- [x] Tests pass

## Status
Implementation Progress:
- Phase 1 (Setup Tests): ✓ PASSED
- Phase 2 (Model Tests): ✓ PASSED
- Phase 3 (API Tests): ✓ PASSED
- Phase 4 (Worker Tests): ✓ PASSED
- Phase 5 (Batch Processor Tests): ✓ PASSED
- Phase 6 (Integration Tests): ✓ PASSED

## Notes
- Removed early proxy assignment to prevent stale proxy/session issues
- Added proxy validation before use
- Simplified batch model (removed proxy/session fields)
- Focus on resilient proxy management
- Each profile check gets fresh, validated proxy
- Added retry logic for rate-limited proxies
- Fixed stats tracking to prevent double-counting
- Added proper error handling and state management
- Added session tracking and cleanup
- Improved rate limit handling with automatic retries
- Added concurrent batch processing prevention

## Key Improvements
1. Just-in-time proxy assignment prevents stale proxy issues
2. Proxy validation ensures reliable story checking
3. Proper proxy rotation and reuse
4. Resilient error handling and retries
5. Clear separation of concerns in test structure
6. Accurate stats tracking with proper state management
7. Automatic retry after rate limits
8. Session cleanup to prevent resource leaks
9. Concurrent batch processing prevention
10. Error clearing after successful retries

## Next Steps
1. ✓ All test phases complete and passing
2. Document final API endpoints and behavior
3. Add monitoring for:
   - Session cleanup verification
   - Rate limit tracking and analysis
   - Proxy health metrics
4. Consider improvements:
   - Batch priority system
   - More sophisticated proxy rotation
   - Enhanced error reporting
