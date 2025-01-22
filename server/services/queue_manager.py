"""
Queue Manager Service
Handles batch queue operations and automatic promotion of batches.

This service manages the queue of batches, including:
- Getting the next available queue position
- Retrieving the currently running batch
- Promoting the next batch in the queue to the running position
- Moving batches to the end of the queue
- Marking batches as completed and automatically promoting the next batch

The QueueManager ensures that batches are processed in order and that
the next batch is automatically started when the current one completes.
"""

from typing import Optional
from flask import current_app
from models import db, Batch
from worker_manager import initialize_worker_pool
from services.batch_log_service import BatchLogService
from services.queue_ordering import reorder_queue

class QueueManager:
    @staticmethod
    def get_next_position() -> int:
        """Get next available queue position"""
        current_app.logger.info("Getting next queue position...")
        last_position = db.session.query(db.func.max(Batch.queue_position))\
            .filter(Batch.queue_position.isnot(None)).scalar()
        next_pos = (last_position or 0) + 1
        current_app.logger.info(f"Next available position: {next_pos}")
        return next_pos

    @staticmethod
    def get_running_batch() -> Optional[Batch]:
        """Get currently running batch (position 0)"""
        current_app.logger.info("Checking for running batch...")
        batch = Batch.query.filter_by(queue_position=0).first()
        if batch:
            current_app.logger.info(f"Found running batch: {batch.id}")
        else:
            current_app.logger.info("No running batch found")
        return batch

    @staticmethod
    def promote_next_batch() -> Optional[Batch]:
        """Promote position 1 to position 0 and start it

        Returns:
            Batch that was promoted, or None if no batch to promote
        """
        current_app.logger.info("=== Promoting Next Batch ===")
        next_batch = Batch.query.filter_by(queue_position=1).first()
        if next_batch:
            current_app.logger.info(f"1. Found next batch: {next_batch.id}")
            BatchLogService.create_log(next_batch.id, 'INFO', f'Found batch to promote')

            # Move to position 0 but keep as queued until processing starts
            current_app.logger.info("2. Moving batch to position 0...")
            next_batch.queue_position = 0
            next_batch.completed_profiles = 0
            next_batch.successful_checks = 0
            next_batch.failed_checks = 0
            BatchLogService.create_log(next_batch.id, 'INFO', f'Moved to position 0')

            # Reset all batch profiles
            current_app.logger.info("3. Resetting batch profiles...")
            for batch_profile in next_batch.profiles:
                batch_profile.status = 'pending'
                batch_profile.has_story = False
                batch_profile.error = None
                batch_profile.processed_at = None
            BatchLogService.create_log(next_batch.id, 'INFO', f'Reset all profiles')

            current_app.logger.info("4. Checking worker pool...")
            if not hasattr(current_app, 'worker_pool'):
                current_app.logger.info("5. Initializing worker pool...")
                initialize_worker_pool(current_app, db)
                BatchLogService.create_log(next_batch.id, 'INFO', f'Initialized worker pool')

            current_app.logger.info("6. Registering batch with worker pool...")
            current_app.worker_pool.register_batch(next_batch.id)
            BatchLogService.create_log(next_batch.id, 'INFO', f'Registered with worker pool')

            db.session.commit()

            # Import and submit after commit to avoid circular imports
            current_app.logger.info("7. Submitting batch for processing...")
            from core.batch_processor import process_batch
            current_app.worker_pool.submit(process_batch, next_batch.id)
            BatchLogService.create_log(next_batch.id, 'INFO', f'Submitted for processing')

            current_app.logger.info("8. Reordering remaining batches...")
            reorder_queue()
            db.session.commit()
            current_app.logger.info("9. Batch promotion complete")

        else:
            current_app.logger.info("No batch found at position 1")

        return next_batch

    @staticmethod
    def move_to_end(batch: Batch) -> None:
        """Move batch to end of queue and reset its progress"""
        if batch:
            current_app.logger.info(f"=== Moving Batch {batch.id} to End ===")

            # Reset batch progress
            current_app.logger.info("1. Resetting batch progress...")
            batch.status = 'queued'
            batch.completed_profiles = 0
            batch.successful_checks = 0
            batch.failed_checks = 0
            BatchLogService.create_log(batch.id, 'INFO', f'Reset batch progress')

            # Reset all batch profiles
            current_app.logger.info("2. Resetting batch profiles...")
            for batch_profile in batch.profiles:
                batch_profile.status = 'pending'
                batch_profile.has_story = False
                batch_profile.error = None
                batch_profile.processed_at = None
            BatchLogService.create_log(batch.id, 'INFO', f'Reset all profiles')

            # Move to end of queue
            current_app.logger.info("3. Moving to end of queue...")
            last_position = db.session.query(db.func.max(Batch.queue_position))\
                .filter(Batch.queue_position.isnot(None)).scalar() or 0
            batch.queue_position = last_position + 1
            BatchLogService.create_log(batch.id, 'INFO', f'Moved to position {batch.queue_position}')

            db.session.commit()
            current_app.logger.info("4. Move to end complete")

    @staticmethod
    def mark_completed(batch_id: str) -> None:
        """Mark batch as completed"""
        batch = db.session.get(Batch, batch_id)
        if batch:
            current_app.logger.info(f"=== Marking Batch {batch.id} Complete ===")
            batch.status = 'done'
            batch.queue_position = None
            BatchLogService.create_log(batch.id, 'INFO', f'Marked as completed')
            db.session.commit()
            current_app.logger.info("Batch marked complete")
            
            current_app.logger.info("Reordering queue after batch completion")
            reorder_queue()
            db.session.commit()
            current_app.logger.info("Queue reordering complete")

            current_app.logger.info("Promoting next batch")
            QueueManager.promote_next_batch()
            current_app.logger.info("Next batch promotion complete")
        else:
            current_app.logger.error(f"Batch {batch_id} not found in mark_completed")
