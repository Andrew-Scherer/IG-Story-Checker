# Batch State Simplification

## Files to Delete
- server/services/safe_state_manager.py (redundant state management)
- server/services/queue_ordering.py (move logic into batch_state_manager)

## Files to Heavily Modify

### 1. server/services/batch_state_manager.py
- Make this the single source of truth for state changes
- Move queue ordering logic here from queue_ordering.py
- Add atomic state transitions with worker pool operations
- Remove redundant state tracking

### 2. server/services/queue_manager.py
- Remove state management code
- Keep only queue position calculation
- Delegate all state changes to batch_state_manager

### 3. server/services/batch_execution_manager.py
- Remove state management code
- Focus only on batch execution logic
- Use batch_state_manager for state changes

### 4. server/api/batch.py
- Remove direct state modifications
- Use batch_state_manager for all state changes
- Simplify resume/stop logic

## Dependencies and Affected Files

### Server-Side Dependencies
1. Core Dependencies:
- server/core/batch_processor.py (imports queue_manager)
- server/core/queue_manager.py (has its own QueueManager class)
- server/core/interfaces/batch_management.py (defines interfaces)

2. API Dependencies:
- server/api/batch.py (imports queue_manager, safe_state_manager, queue_ordering)

3. Test Files to Update:
- server/tests/services/test_batch_management.py
- server/tests/core/test_queue_manager.py
- server/tests/api/test_batch.py

### Client-Side Dependencies
1. React Components:
- client/src/components/batch/BatchTable.jsx (displays status and queue_position)
- client/src/components/niche/NicheFeed.jsx (uses batchStore)

2. State Management:
- client/src/stores/batchStore.js (handles batch operations)
- client/src/api/index.js (API calls for batch operations)

## Core Changes

1. Make BatchStateManager handle everything:
```python
# In batch_state_manager.py
def transition_state(self, batch, new_state, queue_position=None):
    """Single method for all state changes"""
    with db.session.begin_nested():
        if queue_position is not None:
            batch.queue_position = queue_position
        batch.status = new_state
        
        # Handle worker pool in same transaction
        if new_state == 'in_progress':
            current_app.worker_pool.register_batch(batch.id)
        elif batch.status == 'in_progress':
            current_app.worker_pool.unregister_batch(batch.id)
            
        db.session.commit()
```

2. Simplify API endpoints:
```python
# In batch.py
@batch_bp.route('/resume', methods=['POST'])
def resume_batches():
    """Resume paused batches"""
    batch_ids = request.get_json().get('batch_ids', [])
    results = []
    
    for i, batch_id in enumerate(batch_ids):
        batch = db.session.get(Batch, batch_id)
        if not batch:
            continue
            
        # First batch goes to position 0, others get next position
        position = 0 if i == 0 else batch_state_manager.get_next_position()
        batch_state_manager.transition_state(batch, 'in_progress', position)
        results.append(batch.to_dict())
        
    return jsonify(results)
```

## Migration Steps

1. Update BatchStateManager:
   - Add queue ordering logic
   - Add atomic state transitions
   - Add worker pool integration

2. Update API Layer:
   - Remove safe_state_manager imports
   - Remove queue_ordering imports
   - Use batch_state_manager for all state changes

3. Update Tests:
   - Update test_batch_management.py for new state flow
   - Update test_queue_manager.py for simplified queue logic
   - Update test_batch.py for new API behavior

4. Clean Up:
   - Delete safe_state_manager.py
   - Delete queue_ordering.py
   - Remove redundant code from queue_manager.py

No changes needed to client-side code as the API contract remains the same.