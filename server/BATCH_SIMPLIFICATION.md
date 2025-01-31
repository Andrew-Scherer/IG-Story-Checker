# Batch System Simplification Plan

## Overview
The current batch processing system is overengineered with multiple managers, complex state machines, and distributed state management. This plan outlines steps to simplify the system while maintaining core functionality.

## Goals
- Simplify state management
- Reduce code complexity
- Improve maintainability
- Make testing easier
- Keep core batch processing functionality

## Files to Remove
1. [x] server/services/batch_state_manager.py
   - Complex state machine logic
   - Redundant state tracking

2. [x] server/services/queue_manager.py
   - Overly complex queue management
   - Distributed state issues

3. [x] server/services/batch_execution_manager.py
   - Complex async execution
   - Redundant state tracking

4. [x] server/core/interfaces/batch_management.py
   - Unnecessary abstraction layer
   - Complex interface definitions

5. [x] server/services/queue_ordering.py
   - Overcomplicated queue logic
   - Can be simplified into BatchManager

6. [x] server/services/safe_state_manager.py
   - Redundant state safety checks
   - Can be handled by database constraints

## Files to Modify

### 1. server/models/batch.py
Changes:
- [x] Simplify model to basic fields
- [x] Remove complex state validation
- [x] Keep core relationships

```python
class Batch(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    status = db.Column(db.String(20), default='queued')
    position = db.Column(db.Integer, nullable=True, unique=True)  # Unique ensures no position conflicts
    priority = db.Column(db.Integer, default=0)  # Optional: For priority queueing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    profiles = db.relationship('BatchProfile', backref='batch')
```

### 2. server/api/batch.py
Changes:
- [x] Replace manager instances with single BatchManager
- [x] Simplify route handlers
- [x] Remove worker pool initialization
- [x] Clean up error handling

### 3. server/tests/services/test_batch_manager.py
Changes:
- [x] Simplify test setup
- [x] Remove worker pool mocking
- [x] Test core workflows directly
- [x] Add clear state transition tests

### 4. server/tests/conftest.py
Changes:
- [x] Remove worker pool fixture
- [x] Simplify db_session fixture
- [x] Add BatchManager fixture

## Queue Management Design

### Core Queue Operations

```python
class BatchManager:
    def __init__(self, db_session):
        self.db = db_session

    def _get_next_position(self):
        """Get next available queue position"""
        max_pos = self.db.query(func.max(Batch.position))\
            .filter(Batch.position.isnot(None))\
            .scalar()
        return (max_pos or 0) + 1

    def queue_batch(self, batch_id):
        """Add batch to queue"""
        batch = self.db.get(Batch, batch_id)
        if not batch or batch.status == 'running':
            return False
        batch.status = 'queued'
        batch.position = self._get_next_position()
        batch.error = None
        self.db.commit()
        return True

    def start_batch(self, batch_id):
        """Start processing a batch"""
        running = self._get_running_batch()
        if running:
            return False
        batch = self.db.get(Batch, batch_id)
        if not batch or batch.status in ('done', 'error'):
            return False
        batch.status = 'running'
        batch.position = 0  # Position 0 means running
        self.db.commit()
        return True

    def pause_batch(self, batch_id):
        """Pause a batch"""
        batch = self.db.get(Batch, batch_id)
        if not batch or batch.status in ('done', 'error'):
            return False
        batch.status = 'paused'
        batch.position = None  # No position when paused
        self.db.commit()
        self.reorder_queue()
        return True

    def complete_batch(self, batch_id):
        """Mark batch as completed"""
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False
        batch.status = 'done'
        batch.position = None
        batch.completed_at = datetime.now(UTC)
        self.db.commit()
        self.reorder_queue()
        return True

    def handle_error(self, batch_id, error_msg):
        """Handle batch error"""
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False
        batch.status = 'error'
        batch.position = None
        batch.error = error_msg
        self.db.commit()
        self.reorder_queue()
        return True

    def promote_next_batch(self):
        """Promote next batch in queue to running"""
        if self._get_running_batch():
            return None
        next_batch = self.db.query(Batch)\
            .filter(Batch.status == 'queued')\
            .order_by(Batch.position)\
            .first()
        if next_batch:
            next_batch.status = 'running'
            next_batch.position = 0
            self.db.commit()
            self.reorder_queue()
            return next_batch
        return None

    def reorder_queue(self):
        """Reorder queue positions to be sequential"""
        queued_batches = self.db.query(Batch)\
            .filter(Batch.status == 'queued')\
            .order_by(Batch.position)\
            .all()
        new_position = 1  # Start at 1 since 0 is for running
        for batch in queued_batches:
            if batch.position != 0:  # Skip running batch
                batch.position = new_position
                new_position += 1
        self.db.commit()

    def update_progress(self, batch_id, completed=0, successful=0, failed=0):
        """Update batch progress"""
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False
        batch.completed_profiles = completed
        batch.successful_checks = successful
        batch.failed_checks = failed
        if batch.completed_profiles == batch.total_profiles:
            self.complete_batch(batch_id)
        else:
            self.db.commit()
        return True
```

### Queue States
- position = 0: Currently running batch
- position > 0: In queue at that position
- position = None: Not in queue (paused/done/error)

### Benefits
1. Database-Driven
   - Queue position stored directly in database
   - Atomic operations using transactions
   - Clear position management

2. Simple Design
   - Integer-based ordering
   - No complex state machines
   - Easy to query current queue state

3. Race Condition Handling
   - Uses database transactions
   - Unique constraint on position
   - Clear state transitions

4. Easy Maintenance
   - Simple to understand
   - Easy to test
   - Clear debugging

## Implementation Steps

### Phase 1: Core Changes
1. [x] Create new BatchManager class
   - Implemented queue_batch, pause_batch methods
   - Added proper state transitions
   - Added position management
   - Added error handling
   - Added progress tracking
   - Added logging integration
2. [x] Update Batch model
   - Added proper UUID handling
   - Added status and position fields
   - Added relationships for logs and story results
3. [x] Add database migrations
   - Added queue position column
   - Added batch constraints
4. [x] Update API endpoints
   - Fixed transaction handling
   - Added proper state management
   - Improved error handling

### Phase 2: Testing
1. [x] Update test fixtures
   - Added proper UUID handling
   - Fixed session management
   - Added fresh instance fetching
   - Added mock setup helpers
2. [x] Add new BatchManager tests
   - Added proper mock side effects
   - Added state transition tests
   - Added position management tests
   - Added error handling tests
   - Added progress tracking tests
3. [x] Update existing API tests
   - Fixed transaction timing
   - Added proper state assertions
   - Improved error case coverage
4. [ ] Add integration tests

### Phase 3: Client Updates
1. [x] Update batchStore
   - Added simplified states
   - Added position management
   - Added error handling
   - Added log management
2. [x] Update BatchTable component
   - Added queue position display
   - Added state transition handling
   - Added progress tracking
   - Added log viewing
3. [x] Test client changes
   - Added store tests
   - Added component tests
   - Added error case coverage
4. [x] Update error handling
   - Added clear error types
   - Added network error handling
   - Added state transition errors
   - Added concurrent operation handling

### Phase 4: Cleanup
1. [x] Remove old service files
   - Removed safe_state_manager.py (safety via DB constraints)
   - Removed queue_ordering.py (queue logic in BatchManager)
   - Removed batch_execution_manager.py (simplified execution)
   - Removed batch_state_manager.py (state in BatchManager)
2. [x] Remove unused interfaces
   - Removed batch_management.py interface
3. [ ] Clean up dependencies
4. [ ] Update documentation

## Migration Strategy
1. Deploy database changes
2. Deploy new BatchManager
3. Update API endpoints one at a time
4. Deploy client changes
5. Remove old services
6. Verify functionality

## Rollback Plan
1. Keep old services during transition
2. Add feature flag for new system
3. Monitor for issues
4. Ability to revert to old system

## Testing Strategy
1. [x] Unit tests for BatchManager
   - Core operations
   - State transitions
   - Queue management
   - Error handling
2. [ ] Integration tests for API endpoints
3. [ ] End-to-end tests for core workflows
4. [ ] Performance testing for simplified system

## Success Metrics
1. [x] Reduced code complexity
   - Removed 6 service files
   - Simplified state management
   - Centralized queue logic
2. [x] Faster test execution
   - Simplified test setup
   - Removed complex mocking
   - Clear test scenarios
3. [x] Improved maintainability
   - Clear state transitions
   - Database-driven queue
   - Simple error handling
4. [x] No loss of core functionality
   - Queue management works
   - State transitions maintained
   - Progress tracking intact