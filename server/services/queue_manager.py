"""
Queue Manager Service
Handles queue position calculation and batch promotion
"""

from typing import Optional
from flask import current_app
from models import db, Batch
from worker_manager import initialize_worker_pool
from services.batch_log_service import BatchLogService
from services.batch_state_manager import BatchStateManager
from services.batch_execution_manager import BatchExecutionManager

from threading import Lock

class QueueManager:
    """Manages queue positions and batch promotion"""

    def __init__(self):
        """Initialize QueueManager"""
        self.state_manager = BatchStateManager()
        self.execution_manager = BatchExecutionManager(self.state_manager)
        self._update_scheduled = False
        self._lock = Lock()

    def get_next_position(self) -> int:
        """Get next available queue position"""
        return self.state_manager.get_next_position()

    def get_running_batch(self) -> Optional[Batch]:
        """Get currently running batch (position 0)"""
        return self.state_manager.get_running_batch()

    def promote_next_batch(self) -> Optional[Batch]:
        """Promote position 1 to position 0 and start it

        Returns:
            Batch that was promoted, or None if no batch to promote
        """
        current_app.logger.info("=== Promoting Next Batch ===")
        next_batch = db.session.query(Batch).filter_by(queue_position=1).first()
        if next_batch:
            current_app.logger.info(f"1. Found next batch: {next_batch.id}")
            BatchLogService.create_log(next_batch.id, 'INFO', f'Found batch to promote')

            # Initialize worker pool if needed
            current_app.logger.info("2. Checking worker pool...")
            if not hasattr(current_app, 'worker_pool'):
                current_app.logger.info("3. Initializing worker pool...")
                initialize_worker_pool(current_app, db)
                BatchLogService.create_log(next_batch.id, 'INFO', f'Initialized worker pool')

            # Transition state and position atomically
            if self.state_manager.transition_state(next_batch, 'in_progress', 0):
                # Submit for processing
                current_app.logger.info("4. Submitting batch for processing...")
                current_app.worker_pool.submit(self.execution_manager.process_batch, next_batch.id)
                BatchLogService.create_log(next_batch.id, 'INFO', f'Submitted for processing')
                current_app.logger.info("5. Batch promotion complete")
                return next_batch

        current_app.logger.info("No batch found at position 1")
        return None

    def schedule_queue_update(self) -> None:
        """Schedule a queue update if not already scheduled"""
        current_app.logger.info("=== Scheduling Queue Update ===")
        with self._lock:
            if not self._update_scheduled:
                current_app.logger.info("1. Update not already scheduled, scheduling...")
                self._update_scheduled = True
                current_app.worker_pool.submit(self._process_queue_update)
                current_app.logger.info("2. Queue update scheduled")
            else:
                current_app.logger.info("Queue update already scheduled")

    def _process_queue_update(self) -> None:
        """Process queue updates in background"""
        current_app.logger.info("=== Processing Queue Update ===")
        try:
            # Reorder queue positions
            current_app.logger.info("1. Reordering queue...")
            self.state_manager.reorder_queue()
            
            # Promote next batch if needed
            current_app.logger.info("2. Checking for batch promotion...")
            if not self.get_running_batch():
                current_app.logger.info("3. No running batch, promoting next...")
                self.promote_next_batch()
                
        except Exception as e:
            current_app.logger.error(f"Error processing queue update: {e}")
        finally:
            with self._lock:
                self._update_scheduled = False
                current_app.logger.info("4. Queue update complete, cleared scheduled flag")
