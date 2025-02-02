# Starting Batches Again

## Objective

Get the batches running and checking profiles again.

## Critical Tasks

### Task 2: Resolve Proxy Connection Errors

**Description:**

Address connection errors that prevent proxies from being used effectively during story checks.

**Steps:**

- Investigate the `ProxyError - Invalid status line: [` error occurring in `story_checker.py`.
- Test proxy connections independently to ensure they return valid HTTP responses.
- Replace or reconfigure any proxies that are malfunctioning or returning invalid responses.

### Task 3: Fix Exception Handling in `batch_processor.py`

**Description:**

Modify exception handling to prevent errors from halting batch processing and leaving batches in the `running` state.

**Steps:**

- In `batch_processor.py`, sanitize exception messages before logging or saving to the database to prevent `ValueError` due to NUL characters.

  ```python
  except Exception as e:
      error_message = str(e).replace('\x00', '')
      current_app.logger.error(f'Error processing batch: {error_message}')
      batch.failed_checks += 1
      batch.status = 'error'
      self.db.commit()
      BatchLogService.create_log(batch_id, 'BATCH_ERROR', f'Error processing batch: {error_message}')
      self.batch_manager.handle_error(batch_id, error_message)
  ```

- Ensure that batches can recover from errors and continue processing remaining profiles.

### Task 4: Verify Worker Assignment

**Description:**

Ensure that workers are correctly assigned proxy-session pairs and are able to check profiles.

**Steps:**

- Review the `WorkerPool.get_worker()` method in `worker/pool.py` to identify any conditions preventing workers from being assigned.
- Check for issues such as:
  - Worker pool at capacity (`self.active_workers` ≥ `self.max_workers`).
  - No available or healthy proxies.
  - Invalid or expired sessions.
- Address any identified issues to allow workers to be acquired successfully.

### Task 5: Test Batch Processing Workflow

**Description:**

Validate that batches are processing correctly and profiles are being checked.

**Steps:**

- Start a test batch and monitor its progress through the statuses:
  - `queued` → `running` → `completed`.
- Confirm that profiles within the batch are being processed and their statuses update appropriately.
- Check the logs to ensure no critical errors are occurring during processing.
- Verify that batches do not remain stuck in the `running` status.

## Conclusion

By focusing on these critical tasks, we can resolve the issues preventing batches from running and ensure that profiles are checked as intended. Addressing proxy and session validity, fixing exception handling, and verifying worker assignment are essential steps to get the batch processing system operational again.