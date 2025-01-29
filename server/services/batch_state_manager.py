"""
Batch State Manager
Handles batch state transitions and queue management
"""

from typing import Optional
from flask import current_app
from models import db, Batch
from core.interfaces.batch_management import IBatchStateManager
from services.batch_log_service import BatchLogService
from services.queue_ordering import reorder_queue

class BatchStateManager(IBatchStateManager):
    """Manages batch states and queue positions"""
    
    def mark_completed(self, batch_id: str) -> None:
        """Mark a batch as completed
        
        Args:
            batch_id: ID of batch to mark completed
        """
        current_app.logger.info(f"=== Marking Batch {batch_id} Complete ===")
        batch = db.session.get(Batch, batch_id)
        if batch:
            batch.status = 'done'
            batch.queue_position = None
            BatchLogService.create_log(batch.id, 'INFO', f'Marked as completed')
            db.session.commit()
            current_app.logger.info("Batch marked complete")
            
            current_app.logger.info("Reordering queue after batch completion")
            reorder_queue()
            db.session.commit()
            current_app.logger.info("Queue reordering complete")
        else:
            current_app.logger.error(f"Batch {batch_id} not found in mark_completed")
    
    def move_to_end(self, batch: Batch) -> None:
        """Move batch to end of queue and reset its progress
        
        Args:
            batch: Batch to move
        """
        if batch:
            # Get fresh instance from session
            batch = db.session.get(Batch, batch.id)
            if not batch:
                current_app.logger.error(f"Batch {batch.id} not found in move_to_end")
                return

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
            # Ensure profiles are loaded
            db.session.refresh(batch)
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
    
    def update_queue_position(self, batch: Batch, position: int) -> None:
        """Update a batch's queue position
        
        Args:
            batch: Batch to update
            position: New queue position
        """
        if batch:
            # Get fresh instance from session
            batch = db.session.get(Batch, batch.id)
            if not batch:
                current_app.logger.error(f"Batch {batch.id} not found in update_queue_position")
                return

            current_app.logger.info(f"Updating queue position for batch {batch.id} to {position}")
            batch.queue_position = position
            BatchLogService.create_log(batch.id, 'INFO', f'Updated queue position to {position}')
            db.session.commit()
            current_app.logger.info("Queue position update complete")
    
    def get_running_batch(self) -> Optional[Batch]:
        """Get currently running batch (position 0)
        
        Returns:
            Currently running batch or None
        """
        current_app.logger.info("Checking for running batch...")
        batch = Batch.query.filter_by(queue_position=0).first()
        if batch:
            current_app.logger.info(f"Found running batch: {batch.id}")
        else:
            current_app.logger.info("No running batch found")
        return batch