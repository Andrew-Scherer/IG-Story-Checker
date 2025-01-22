# Debugging `batch_processor.py` and `story_checker.py`

This document outlines the phases and associated to-dos for addressing the critical issues identified in the batch processing and story checking components. The most critical errors and suggestions are prioritized at the top.

---

## Phase 1: Critical Fixes

### 1. Correct Success Logging in `batch_processor.py`

**Issue:**

- The `STORY_CHECK_SUCCESS` log is created immediately after calling `worker.check_story` without verifying if the story check actually succeeded. This may result in successes being logged even when the story check fails or doesn't occur.

**To-Dos:**

- **Modify `batch_processor.py`:**
  - Update the logic to log `STORY_CHECK_SUCCESS` only after confirming that the story check was successful.
  - Ensure that the success log is created only when `success` is `True` and the story check has been verified.

### 2. Enhance Error Handling and Logging

**Issue:**

- Exceptions and failures within `worker.check_story` and `story_checker.check_story` are not adequately logged or reported back to the batch processor. Failures are not reflected in the batch logs, making it seem like all checks are successful.

**To-Dos:**

- **In `worker.py`:**
  - Ensure that exceptions raised in `story_checker.check_story` are properly caught and propagated.
  - Return meaningful error messages back to `batch_processor.py`.

- **In `batch_processor.py`:**
  - Add error logging for failed checks using `BatchLogService.create_log` with event types like `CHECK_FAILED`.
  - Include detailed error messages in the logs to aid debugging.

### 3. Correct Batch Counter Updates

**Issue:**

- The `batch.completed_profiles` counter is only incremented on success. If a profile check fails, it may not be counted as completed, leading to inaccurate batch summaries. Additionally, `batch.failed_checks` may not be incremented appropriately.

**To-Dos:**

- **In `batch_processor.py`:**
  - Increment `batch.completed_profiles` regardless of success or failure to reflect the total number of profiles processed.
  - Increment `batch.failed_checks` appropriately when a profile check fails.
  - Ensure batch summaries accurately reflect the number of successful and failed checks.

---

## Phase 2: Improve Exception Handling

### 4. Proper Exception Handling in `story_checker.py`

**Issue:**

- The `check_story` method may exit prematurely due to exceptions (e.g., rate limiting, API failures) without performing the actual story check. Exceptions are raised but not properly handled, leading to immediate returns without checking the profile.

**To-Dos:**

- **Implement Robust Exception Handling:**
  - Catch specific exceptions for rate limiting and API errors.
  - Add retry logic for transient errors, with a maximum number of retries and appropriate delays.
  - Ensure that exceptions are logged with detailed messages for easier debugging.

- **Propagate Exceptions Upstream:**
  - Raise exceptions with meaningful messages so that they can be handled in `worker.py` and `batch_processor.py`.

---

## Phase 3: Logging Consolidation

### 5. Consolidate Logging for Better Visibility

**Issue:**

- Detailed logs from `story_checker.py` are written to `server/logs/story_checking.log` and are not reflected in the batch logs. This separation makes debugging difficult, as important error messages are not visible during batch processing.

**To-Dos:**

- **Integrate Logging:**
  - Configure `story_checker.py` to use a shared logger or logging configuration that feeds into the main batch logs.
  - Ensure that critical errors and events are logged in a way that they are visible during batch processing.

- **Update Logging Configuration:**
  - Review the logging setup to prevent duplicate handlers and unnecessary console output.
  - Standardize log formats and levels across modules for consistency.

---

## Phase 4: Code Maintenance and Improvements

### 6. Review Success Handling Criteria

**Issue:**

- Success may be recorded even when the actual story check did not occur or failed, due to improper handling of the `success` flag.

**To-Dos:**

- **Audit Success Conditions:**
  - Review the conditions under which `success` is set to `True` in `worker.py` and `batch_processor.py`.
  - Ensure that `success` is only `True` when the story check completes without exceptions and valid results are obtained.

### 7. Add Detailed Error Messages

**Issue:**

- Error messages may be too generic, making it difficult to diagnose issues.

**To-Dos:**

- **Enhance Error Messages:**
  - Include relevant information such as profile usernames, proxy details, and exception specifics in error logs.
  - Provide stack traces or error codes where appropriate.

---

## Phase 5: Additional Improvements

### 8. Implement Retry Mechanisms

**Issue:**

- There is limited retry logic for handling rate limiting and transient network issues.

**To-Dos:**

- **Enhance Retry Logic:**
  - Implement exponential backoff strategies when retries are necessary.
  - Introduce configurable parameters for maximum retries and wait times.

### 9. Optimize Proxy Handling

**Issue:**

- Proxies may become disabled due to failures without proper validation.

**To-Dos:**

- **Improve Proxy Session Management:**
  - Validate proxies periodically to ensure they are still functioning.
  - Implement failover mechanisms to switch to alternative proxies when issues are detected.
