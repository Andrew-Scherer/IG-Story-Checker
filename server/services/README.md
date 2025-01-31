# Services Layer

Core business logic and service implementations.

## Components

### BatchManager
- Core batch state and queue management
- Single source of truth for batch operations
- Handles state transitions and queue positions
- Manages batch completion and errors

### BatchExecutionManager
- Handles batch processing and execution
- Manages worker allocation
- Processes batch profiles
- Handles execution errors

### BatchLogService
- Handles batch operation logging
- Records state changes and errors
- Tracks batch progress

### StoryService
- Handles story checking operations
- Manages story detection results
- Records story check history

## Design Principles

1. **Single Responsibility**
   - Each service handles one core aspect
   - Clear separation of concerns
   - Focused functionality

2. **State Management**
   - Database as source of truth
   - Atomic operations
   - Clear state transitions

3. **Error Handling**
   - Consistent error patterns
   - Proper logging
   - Error recovery

4. **Queue Management**
   - Simple position-based queueing
   - Clear batch ordering
   - Atomic position updates

## Usage

```python
# Initialize services
batch_manager = BatchManager(db.session)
execution_manager = BatchExecutionManager(batch_manager)

# Queue a batch
batch_manager.queue_batch(batch_id)

# Process batch
execution_manager.process_batch(batch_id)