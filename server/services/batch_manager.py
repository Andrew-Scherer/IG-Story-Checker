"""
Batch Manager
Handles batch state and queue management
"""

from datetime import datetime, UTC
from sqlalchemy import func
from models import db, Batch
from services.batch_log_service import BatchLogService

BATCH_STATES = {
    'queued',   # In queue with position > 0
    'running',  # Currently processing (position = 0)
    'paused',   # Stopped (position = null)
    'done',     # Completed (position = null)
    'error'     # Failed (position = null)
}

class BatchManager:
    """Manages batch state and queue operations"""

    def __init__(self, db_session):
        """Initialize BatchManager
        
        Args:
            db_session: Database session for batch operations
        """
        self.db = db_session

    def _get_next_position(self):
        """Get next available queue position"""
        max_pos = self.db.query(func.max(Batch.position))\
            .filter(Batch.position.isnot(None))\
            .scalar()
        return (max_pos or 0) + 1

    def _get_running_batch(self):
        """Get currently running batch"""
        return self.db.query(Batch)\
            .filter(Batch.position == 0)\
            .first()

    def queue_batch(self, batch_id):
        """Add batch to queue
        
        Args:
            batch_id: ID of batch to queue
            
        Returns:
            bool: True if queued successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False
            
        # Only allow queuing if not already running or completed
        if batch.status in ('running', 'done', 'error'):
            return False

        # Queue the batch
        batch.status = 'queued'
        batch.position = self._get_next_position()
        batch.error = None
        BatchLogService.create_log(
            batch_id,
            'STATE_CHANGE',
            f'Status changed to queued at position {batch.position}'
        )
        self.db.commit()
        return True

    def start_batch(self, batch_id):
        """Start processing a batch
        
        Args:
            batch_id: ID of batch to start
            
        Returns:
            bool: True if started successfully
        """
        # Check if another batch is running
        running = self._get_running_batch()
        if running:
            return False

        batch = self.db.get(Batch, batch_id)
        if not batch or batch.status in ('done', 'error'):
            return False

        batch.status = 'running'
        batch.position = 0  # Position 0 means running
        batch.error = None
        BatchLogService.create_log(
            batch_id,
            'STATE_CHANGE',
            'Status changed to running at position 0'
        )
        self.reorder_queue()  # Updates positions
        self.db.commit()  # Commit both state change and queue reordering
        return True

    def pause_batch(self, batch_id):
        """Pause a batch
        
        Args:
            batch_id: ID of batch to pause
            
        Returns:
            bool: True if paused successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch or batch.status in ('done', 'error'):
            return False

        batch.status = 'paused'
        batch.position = None  # No position when paused
        BatchLogService.create_log(
            batch_id,
            'STATE_CHANGE',
            'Status changed to paused'
        )
        self.reorder_queue()  # Updates positions
        self.db.commit()  # Commit both state change and queue reordering
        return True

    def complete_batch(self, batch_id):
        """Mark batch as completed
        
        Args:
            batch_id: ID of batch to complete
            
        Returns:
            bool: True if completed successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False

        batch.status = 'done'
        batch.position = None
        batch.completed_at = datetime.now(UTC)
        BatchLogService.create_log(
            batch_id,
            'STATE_CHANGE',
            'Status changed to done'
        )
        self.reorder_queue()  # Updates positions
        self.db.commit()  # Commit both state change and queue reordering
        return True

    def handle_error(self, batch_id, error_msg):
        """Handle batch error
        
        Args:
            batch_id: ID of failed batch
            error_msg: Error message
            
        Returns:
            bool: True if error handled successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False

        batch.status = 'error'
        batch.position = None
        batch.error = error_msg
        BatchLogService.create_log(
            batch_id,
            'ERROR',
            error_msg
        )
        self.reorder_queue()  # Updates positions
        self.db.commit()  # Commit both state change and queue reordering
        return True

    def promote_next_batch(self):
        """Promote next batch in queue to running
        
        Returns:
            Batch: Promoted batch or None
        """
        # Check if a batch is already running
        if self._get_running_batch():
            return None

        # Get next batch in queue
        next_batch = self.db.query(Batch)\
            .filter(Batch.status == 'queued')\
            .order_by(Batch.position)\
            .first()

        if next_batch:
            next_batch.status = 'running'
            next_batch.position = 0  # Position 0 means running
            self.db.flush()  # Use self.db instead of db.session
            BatchLogService.create_log(
                next_batch.id,
                'STATE_CHANGE',
                'Status changed to running at position 0'
            )
            self.reorder_queue()  # Updates positions
            self.db.commit()  # Commit both state change and queue reordering
            return next_batch

        return None

    def reorder_queue(self):
        """Reorder queue positions to be sequential after state changes
        
        This is a helper method that updates queue positions but does not commit.
        The caller is responsible for committing the transaction.
        """
        # Get all queued batches
        queued_batches = self.db.query(Batch)\
            .filter(Batch.status == 'queued')\
            .order_by(Batch.position)\
            .all()

        # Start at position 1 since 0 is reserved for running batch
        new_position = 1
        for batch in queued_batches:
            if batch.position != 0:  # Skip running batch
                batch.position = new_position
                BatchLogService.create_log(
                    batch.id,
                    'QUEUE_UPDATE',
                    f'Updated queue position to {new_position}'
                )
                new_position += 1

    def update_progress(self, batch_id, completed=0, successful=0, failed=0):
        """Update batch progress
        
        Args:
            batch_id: ID of batch to update
            completed: Number of completed profiles
            successful: Number of successful checks
            failed: Number of failed checks
            
        Returns:
            bool: True if progress updated successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False

        batch.completed_profiles = completed
        batch.successful_checks = successful
        batch.failed_checks = failed

        BatchLogService.create_log(
            batch_id,
            'PROGRESS',
            f'Updated progress: {completed}/{batch.total_profiles} completed'
        )

        # Auto-complete if all profiles processed
        if batch.completed_profiles == batch.total_profiles:
            self.complete_batch(batch_id)
        else:
            self.db.commit()

        return True

    def reset_batch(self, batch_id):
        """Reset batch to initial state
        
        Args:
            batch_id: ID of batch to reset
            
        Returns:
            bool: True if reset successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False

        batch.status = 'queued'
        batch.position = self._get_next_position()
        batch.completed_profiles = 0
        batch.successful_checks = 0
        batch.failed_checks = 0
        batch.completed_at = None
        batch.error = None
        
        BatchLogService.create_log(
            batch_id,
            'STATE_CHANGE',
            f'Reset to queued at position {batch.position}'
        )
        self.db.commit()
        return True