# Batch Queue System Documentation

## Overview

The batch queue system introduces queuing and automation to manage batch processing efficiently. It ensures that batches are processed in order and provides automation for starting subsequent batches without manual intervention.

## Key Features

1. **Batch Queuing**: When multiple batches are created, they are placed in a queue based on their creation order. Only one batch is processed at a time.

2. **Automated Batch Processing**: Once a batch completes processing, the next batch in the queue automatically starts.

3. **Queue Position Tracking**: Each batch is assigned a `queue_position` to indicate its place in the queue. This is visible in the user interface.

4. **Real-time Status Updates**: Batches update their status throughout the processing lifecycle, allowing users to monitor progress.

## How It Works

### Batch Creation

- **No Running Batch**:
  - If there is no batch currently running, the new batch starts processing immediately.
  - The batch `status` is set to `'queued'` initially and then updated to `'in_progress'`.
  - The `queue_position` is set to `0`.

- **Existing Running Batch**:
  - If a batch is already running, the new batch is added to the queue.
  - The batch `status` is set to `'queued'`.
  - The `queue_position` is set to the next available position in the queue.

### Batch Processing

- The batch processor handles one batch at a time.
- When a batch completes processing:
  - Its `status` is updated to `'done'`.
  - Its `queue_position` is cleared (`None`).
- The system then automatically promotes the next batch in the queue:
  - The next batch's `status` is updated from `'queued'` to `'in_progress'`.
  - Its `queue_position` is updated to `0`.
  - Processing begins automatically without manual intervention.

## User Interface Updates

- **Batch Table**:
  - A **Queue Position** column displays each batch's position in the queue.
  - Queued batches display their position (e.g., `#1`, `#2`).
  - The running batch shows `0` or `In Progress`.
  - Completed batches display `-` or are left blank in the queue position column.

- **Start Button Logic**:
  - The **Start** button is disabled when there are batches in the queue.
  - Users cannot start multiple batches manually; batches are managed automatically.
  - The **Start** button becomes enabled when there are no running or queued batches.

## Managing Batches

### Creating Batches

- Navigate to the batch creation page.
- Select the profiles and parameters for the batch.
- Submit the batch for processing.
- The batch will either start immediately or be added to the queue based on the current system state.

### Monitoring Batches

- View the **Batch Table** to see all batches, their statuses, and queue positions.
- Click on a batch to view detailed logs and progress reports.
- Batches update their status in real-time.

### Stopping Batches

- **Stopping the Running Batch**:
  - Users can stop the currently running batch if necessary.
  - The batch's `status` will be updated, and processing will halt.
  - The next batch in the queue will not start automatically until the user initiates it.

- **Managing Queued Batches**:
  - Queued batches can be reordered or removed from the queue.
  - Adjusting the queue positions allows prioritizing certain batches.

## Technical Details

### Database Changes

- The `Batch` model (`server/models/batch.py`) includes:
  ```python
  queue_position = Column(Integer, nullable=True)
  ```
- This field tracks the batch's position in the queue.

### Backend Logic

- **Batch Creation Logic** (`server/api/batch.py`):
  - Checks if a batch is currently running using `QueueManager.get_running_batch()`.
  - Assigns `queue_position` and `status` based on whether a batch is running.

- **Automatic Batch Promotion** (`server/core/batch_processor.py`):
  - After a batch completes, `QueueManager.promote_next_batch()` is called.
  - This function updates the next queued batch to start processing.

- **Queue Management** (`server/services/queue_manager.py`):
  - Provides methods to manage the batch queue.
  - Key functions:
    - `get_running_batch()`
    - `get_next_position()`
    - `promote_next_batch()`

### Frontend Updates

- **BatchTable Component** (`client/src/components/batch/BatchTable.jsx`):
  - Added a new column to display `queue_position`.
  - Updated the **Start** button logic to disable it when batches are queued or running.

## Best Practices

- **Avoid Manual Interference**:
  - Allow the system to manage batch processing automatically.
  - Only stop batches if absolutely necessary.

- **Monitor Batch Progress**:
  - Regularly check batch statuses and logs.
  - Identify and address any failures promptly.

- **Manage Queue Wisely**:
  - Prioritize batches by adjusting their positions if needed.
  - Remove unnecessary batches from the queue to optimize processing.

## Troubleshooting

- **Batch Not Starting Automatically**:
  - Ensure that the previous batch has completed.
  - Check for any errors in batch logs that may prevent automatic promotion.

- **Cannot Start a New Batch**:
  - The **Start** button is disabled when batches are queued or running.
  - Wait for the current batches to complete or manage the queue to allow new batches.

- **Batch Stuck in Queue**:
  - Verify that the worker pool is active and has available workers.
  - Check the application logs for any errors related to batch processing.

## Recent Improvements

The batch queue system has been recently enhanced to provide even more efficient and automated processing:

- **Automatic Batch Promotion**: When a batch completes, the system now automatically promotes and starts the next batch in the queue without any manual intervention.
- **Continuous Processing**: The queue is continuously monitored and managed, ensuring that batches are processed in order and without delays between batches.
- **Improved Error Handling**: The system now handles errors more gracefully, ensuring that if a batch fails, it doesn't block the entire queue from processing.

These improvements further reduce the need for manual oversight and increase the overall efficiency of the batch processing system.

## Conclusion

The batch queue system significantly enhances the application's ability to handle multiple batches efficiently. By fully automating batch promotion, providing clear visibility into batch statuses and queue positions, and improving error handling, the system streamlines workflow and minimizes the need for manual intervention. This results in a more robust, efficient, and user-friendly batch processing experience.
