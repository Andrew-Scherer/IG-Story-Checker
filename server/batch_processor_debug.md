# Batch Processor Debug Plan

This document outlines the phases of the batch processing workflow and the tasks to be completed under each phase to achieve full functionality from Batch Start to Batch Finish, including updating profiles with active stories and statistics.

---

## Phase 1: Batch Initialization

**Goals:**
- Ensure batches are properly initialized and ready for processing.

**Tasks:**
- [ ] Verify that batches are created with the correct initial status (`queued`).
- [ ] Confirm that batch profiles are correctly associated with their batches.
- [ ] Ensure that the `start_batches` endpoint updates the batch status to `in_progress`.
- [ ] Log batch start events using `BatchLogService`.

---

## Phase 2: Worker Pool Setup

**Goals:**
- Set up the worker pool to manage worker instances for processing profiles.

**Tasks:**
- [ ] Initialize the `WorkerPool` with the correct maximum number of workers.
- [ ] Populate the `ProxyManager` with available proxies and sessions.
- [ ] Ensure that workers can be retrieved using `worker_pool.get_worker()`.
- [ ] Implement the `is_available()` method in the `Worker` class to check worker availability.
- [ ] Log worker pool status and worker assignments.

---

## Phase 3: Batch Processing Loop

**Goals:**
- Process each profile in the batch, checking for active stories.

**Tasks:**
- [ ] Iterate over `batch.profiles` and process each `BatchProfile`.
- [ ] For each profile:
  - [ ] Acquire an available worker from the `WorkerPool`.
  - [ ] Handle cases where no workers are available (e.g., wait and retry).
  - [ ] Use the worker to check for stories (`worker.check_story(batch_profile)`).
  - [ ] Implement retry logic for rate limits and failed attempts.
  - [ ] Update `batch_profile` status (`completed` or `failed`) based on the result.
  - [ ] Log profile check start and end events.

---

## Phase 4: Error Handling and Recovery

**Goals:**
- Robustly handle errors to prevent batch processing from halting unexpectedly.

**Tasks:**
- [ ] Implement comprehensive exception handling throughout the batch processing code.
- [ ] On exceptions, log detailed error information using `BatchLogService`.
- [ ] Ensure that workers are released back to the pool in all cases (use `finally` blocks).
- [ ] Update `batch_profile.status` to `failed` and record the error message.

---

## Phase 5: Batch Completion and Statistics Update

**Goals:**
- Finalize batch processing and update batch statistics.

**Tasks:**
- [ ] Update `batch.completed_profiles` after processing all profiles.
- [ ] Calculate and update `batch.successful_checks` and `batch.failed_checks`.
- [ ] Set the batch status to `done` upon completion.
- [ ] Commit all changes to the database.
- [ ] Log batch completion events with summary statistics.

---

## Phase 6: Profile Updates

**Goals:**
- Update profiles with the results from the story checks.

**Tasks:**
- [ ] For profiles with active stories:
  - [ ] Set `profile.active_story` to `True`.
  - [ ] Update `profile.last_story_detected` with the current timestamp.
- [ ] For profiles without active stories:
  - [ ] Set `profile.active_story` to `False`.
- [ ] Increment `profile.total_checks` and `profile.total_detections` accordingly.
- [ ] Commit profile changes to the database.

---

## Phase 7: Logging and Monitoring

**Goals:**
- Ensure detailed logging for monitoring and debugging purposes.

**Tasks:**
- [ ] Use `BatchLogService` to log key events and status updates throughout processing.
- [ ] Implement logging levels (INFO, WARNING, ERROR) appropriately.
- [ ] Ensure timestamps and relevant identifiers (batch ID, profile ID, proxy ID) are included in logs.
- [ ] Review logs regularly to identify any unexpected behavior.

---

## Phase 8: Testing and Validation

**Goals:**
- Verify that the batch processing workflow functions as expected.

**Tasks:**
- [ ] Write unit tests for individual components (e.g., `WorkerPool`, `Worker`, `BatchProcessor`).
- [ ] Create integration tests that simulate end-to-end batch processing.
- [ ] Test with various batch sizes and profile configurations.
- [ ] Validate that profiles and batches are correctly updated in the database.
- [ ] Confirm that error handling works by inducing failures and observing recovery.

---

## Phase 9: Optimization and Scaling

**Goals:**
- Enhance performance and prepare for scaling to larger workloads.

**Tasks:**
- [ ] Optimize database queries and reduce unnecessary commits.
- [ ] Implement asynchronous processing where beneficial.
- [ ] Profile the application to identify bottlenecks.
- [ ] Consider implementing a task queue system (e.g., Celery, RQ) for better scalability.
- [ ] Evaluate the worker pool management strategy for efficiency.

---

## Phase 10: Documentation and Deployment

**Goals:**
- Document the batch processing system and prepare it for deployment.

**Tasks:**
- [ ] Update code comments and docstrings for clarity.
- [ ] Create or update documentation for developers (e.g., setup guides, API docs).
- [ ] Ensure configuration files are properly set up for different environments (development, testing, production).
- [ ] Test deployment procedures and scripts.
- [ ] Monitor the application post-deployment to ensure stability.

---

By working through these phases and tasks, we aim to achieve a fully functional and robust batch processing system that can handle the entire workflow from start to finish.
