"""
Queue Manager Service
Handles batch queue operations and automatic promotion of batches.

This service manages the queue of batches, including:
- Getting the next available queue position
- Retrieving the currently running batch
- Promoting the next batch in the queue to the running position
- Moving batches to the end of the queue
- Marking batches as completed and automatically promoting the next batch
"""

from typing import Optional
from flask import current_app
from models import db, Batch
from worker_manager import initialize_worker_pool
from services.batch_log_service import BatchLogService
from services.batch_state_manager import BatchStateManager
from services.batch_execution_manager import BatchExecutionManager
from core.interfaces.batch_management import IBatchStateManager, IBatchExecutionManager

class QueueManager:
    """Manages batch queue operations using state and execution managers"""

    def __init__(self):
        """Initialize QueueManager with state and execution managers"""
        self.state_manager = BatchStateManager()
        self.execution_manager = BatchExecutionManager(self.state_manager)

    @staticmethod
    def get_next_position() -> int:
        """Get next available queue position"""
        current_app.logger.info("Getting next queue position...")
        last_position = db.session.query(db.func.max(Batch.queue_position))\
            .filter(Batch.queue_position.isnot(None)).scalar()
        next_pos = (last_position or 0) + 1
        current_app.logger.info(f"Next available position: {next_pos}")
        return next_pos

    def get_running_batch(self) -> Optional[Batch]:
        """Get currently running batch (position 0)"""
        return self.state_manager.get_running_batch()

    def promote_next_batch(self) -> Optional[Batch]:
        """Promote position 1 to position 0 and start it

        Returns:
            Batch that was promoted, or None if no batch to promote
        """
        current_app.logger.info("=== Promoting Next Batch ===")
        next_batch = Batch.query.filter_by(queue_position=1).first()
        if next_batch:
            current_app.logger.info(f"1. Found next batch: {next_batch.id}")
            BatchLogService.create_log(next_batch.id, 'INFO', f'Found batch to promote')

            # Move to position 0
            current_app.logger.info("2. Moving batch to position 0...")
            self.state_manager.update_queue_position(next_batch, 0)
            BatchLogService.create_log(next_batch.id, 'INFO', f'Moved to position 0')

            current_app.logger.info("3. Checking worker pool...")
            if not hasattr(current_app, 'worker_pool'):
                current_app.logger.info("4. Initializing worker pool...")
                initialize_worker_pool(current_app, db)
                BatchLogService.create_log(next_batch.id, 'INFO', f'Initialized worker pool')

            current_app.logger.info("5. Registering batch with worker pool...")
            current_app.worker_pool.register_batch(next_batch.id)
            BatchLogService.create_log(next_batch.id, 'INFO', f'Registered with worker pool')

            # Execute batch
            current_app.logger.info("6. Submitting batch for processing...")
            current_app.worker_pool.submit(self.execution_manager.execute_batch, next_batch.id)
            BatchLogService.create_log(next_batch.id, 'INFO', f'Submitted for processing')

            current_app.logger.info("7. Batch promotion complete")

        else:
            current_app.logger.info("No batch found at position 1")

        return next_batch

    def move_to_end(self, batch: Batch) -> None:
        """Move batch to end of queue and reset its progress"""
        self.state_manager.move_to_end(batch)

    def mark_completed(self, batch_id: str) -> None:
        """Mark batch as completed and promote next batch"""
        self.state_manager.mark_completed(batch_id)
        self.promote_next_batch()

# Create singleton instance
queue_manager = QueueManager()
