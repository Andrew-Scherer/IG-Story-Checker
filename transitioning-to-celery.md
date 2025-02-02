# Transitioning to Celery

This document outlines the plan to transition our background job processing to use Celery. Below are the files affected and the changes we have made, organized into phases. Phases 1, 2, and 3 are now complete.

---

## Phase 1: Set Up Celery and Refactor Core Processing

### Affected Files:

#### 1. `server/core/batch_processor.py`

- **Changes:**
  - Refactored `BatchProcessor` to use Celery tasks.
  - Replaced custom asynchronous code with Celery task calls.
- [x] Refactored `process_batches` to enqueue Celery tasks.
- [x] Removed `asyncio` loops and custom worker acquisition logic.

#### 2. `server/core/worker/pool.py`

- **Changes:**
  - Removed the `WorkerPool` class.
  - Eliminated threading and custom worker management.
- [x] Extracted necessary logic before removing `WorkerPool`.
- [x] Updated all references to `WorkerPool` in other modules.

#### 3. `server/core/worker/worker.py`

- **Changes:**
  - Adapted `Worker` methods into Celery tasks.
  - Ensured compatibility with Celery's task execution model.
- [x] Refactored `Worker` methods into standalone functions or tasks.
- [x] Ensured error handling aligns with Celery's retry mechanisms.

### Phase 1 Summary:

- Set up Celery in the project.
- Refactored core batch processing to use Celery tasks.
- Removed custom worker pool implementation.

---

## Phase 2: Integrate Proxy and Session Management with Celery

### Affected Files:

#### 4. `server/core/proxy_manager.py` and `server/core/session_manager.py`

- **Changes:**
  - Merged `proxy_manager.py` and `session_manager.py` into `proxy_session_manager.py`.
  - Updated proxy and session management to work within Celery tasks.
  - Ensured proxies are correctly managed during task execution.
- [x] Refactored `ProxyManager` and `SessionManager` methods for thread-safe operation.
- [x] Ensured proper handling of proxies in distributed tasks.
- [x] Updated `ProxySessionManager` to be compatible with Celery.
- [x] Tested session retrieval and storage in tasks.

### Phase 2 Summary:

- Merged proxy and session management into `proxy_session_manager.py`.
- Integrated proxy and session management within Celery tasks.
- Ensured resource management is compatible with Celery's architecture.

---

## Phase 3: Update Configuration, Logging, and Testing

### Affected Files:

#### 6. `server/app.py`

- **Changes:**
  - Configured Celery application and integrated with Flask.
  - Set up message broker connections (e.g., Redis or RabbitMQ).
- [x] Initialized Celery instance in `app.py`.
- [x] Updated application factory to include Celery.

#### 7. `server/config.py`

- **Changes:**
  - Added Celery configuration settings.
- [x] Added broker URL and backend settings for Celery.
- [x] Included Celery-specific configurations.

#### 8. `server/requirements.txt`

- **Changes:**
  - Added Celery and message broker dependencies.
- [x] Added `celery` to the requirements.
- [x] Included necessary broker packages (e.g., `redis`).

#### 9. Tests in `server/tests/`

- **Changes:**
  - Updated tests to accommodate Celery.
- [x] Refactored existing tests for the new task-based model.
- [x] Utilized Celery's testing utilities.

### Phase 3 Summary:

- Updated configuration files for Celery integration.
- Modified logging and error handling as needed.
- Updated tests to use Celery's testing utilities.

---

## Overall To-Do List:

### Phase 1 Tasks:

- [x] Set up Celery in the project environment.
- [x] Refactored `server/core/batch_processor.py` to use Celery tasks.
- [x] Removed custom worker pool by refactoring `server/core/worker/pool.py`.
- [x] Adapted `server/core/worker/worker.py` methods into Celery tasks.

### Phase 2 Tasks:

- [x] Merged `proxy_manager.py` and `session_manager.py` into `proxy_session_manager.py`.
- [x] Updated `ProxySessionManager` for compatibility with Celery.
- [x] Ensured proper handling of proxies in distributed tasks.
- [x] Ensured thread-safe operation of resource managers.

### Phase 3 Tasks:

- [x] Configured Celery in `server/app.py` and `server/config.py`.
- [x] Added Celery dependencies to `server/requirements.txt`.
- [x] Updated application factory to include Celery.
- [x] Added broker URL and backend settings for Celery.
- [x] Included Celery-specific configurations.
- [x] Updated and refactored tests in `server/tests/` for Celery.
- [x] Utilized Celery's testing utilities.

---

**Progress Summary:**

We have successfully completed all phases of the transition plan:

- **Phase 1**: Core functionality has been migrated to use Celery tasks.
- **Phase 2**: Proxy and session management have been consolidated and integrated with Celery.
- **Phase 3**: Configuration, testing, and logging have been updated to support Celery.

**Completed Changes:**

1. Core Changes:
   - Removed custom worker pool implementation
   - Refactored batch processing to use Celery tasks
   - Merged proxy and session management

2. Configuration:
   - Added Celery settings to `config.py`
   - Updated Flask application factory
   - Added required dependencies

3. Testing:
   - Removed obsolete test files
   - Updated `test_batch_processor.py` to use Celery's testing utilities
   - Added Celery-specific test configurations

The transition to Celery is now complete, providing a more robust and maintainable background job processing system.