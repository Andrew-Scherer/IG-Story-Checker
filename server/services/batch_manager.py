"""
Batch Manager
Handles batch state, queue management, and concurrency control
"""

from datetime import datetime, UTC
from sqlalchemy import func
from models import db, Batch
from services.batch_log_service import BatchLogService

BATCH_STATES = {
    'queued',   # In queue with position > 0
    'running',  # Currently processing (position <= max_concurrent_batches)
    'paused',   # Stopped (position = null)
    'done',     # Completed (position = null)
    'error'     # Failed (position = null)
}

class BatchManager:
    """Manages batch state, queue operations, and concurrency limits"""

    def __init__(self, db_session, max_concurrent_batches=2):
        """Initialize BatchManager
        
        Args:
            db_session: Database session for batch operations
            max_concurrent_batches: Maximum number of batches that can run concurrently
        """
        self.db = db_session
        self.max_concurrent_batches = max_concurrent_batches

    def _get_next_position(self):
        """Get next available queue position"""
        max_pos = self.db.query(func.max(Batch.position))\
            .filter(Batch.position.isnot(None))\
            .scalar()
        return (max_pos or 0) + 1

    def _get_running_batches(self):
        """Get currently running batches"""
        return self.db.query(Batch)\
            .filter(Batch.status == 'running')\
            .order_by(Batch.position)\
            .all()

    def _get_running_batch_count(self):
        """Get count of currently running batches"""
        return self.db.query(Batch)\
            .filter(Batch.status == 'running')\
            .count()

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
        """Start processing a batch if concurrency limits allow
        
        Args:
            batch_id: ID of batch to start
            
        Returns:
            bool: True if started successfully
        """
        # Check concurrency limit
        running_count = self._get_running_batch_count()
        if running_count >= self.max_concurrent_batches:
            return False

        batch = self.db.get(Batch, batch_id)
        if not batch or batch.status in ('done', 'error'):
            return False

        batch.status = 'running'
        batch.position = self._get_running_batch_positions() + 1
        batch.error = None
        BatchLogService.create_log(
            batch_id,
            'STATE_CHANGE',
            f'Status changed to running at position {batch.position}'
        )
        self.reorder_queue()  # Updates positions
        self.db.commit()  # Commit both state change and queue reordering
        return True

    def _get_running_batch_positions(self):
        """Get the highest position among running batches"""
        max_pos = self.db.query(func.max(Batch.position))\
            .filter(Batch.status == 'running')\
            .scalar()
        return max_pos or 0

    def pause_batch(self, batch_id):
        """Pause a batch
        
        Args:
            batch_id: ID of batch to pause
            
        Returns:
            bool: True if paused successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch or batch.status == 'done':
            return False

        batch.status = 'paused'
        batch.position = None  # No position when paused
        BatchLogService.create_log(
            batch_id,
            'STATE_CHANGE',
            'Status changed to paused'
        )
        self.reorder_queue()  # Updates positions
        self.db.commit()
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
        self.db.commit()
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
        self.db.commit()
        return True

    def promote_next_batch(self):
        """Promote next batch in queue to running if concurrency limits allow
        
        Returns:
            Batch: Promoted batch or None
        """
        # Check concurrency limit
        running_count = self._get_running_batch_count()
        if running_count >= self.max_concurrent_batches:
            return None

        # Get next batch in queue
        next_batch = self.db.query(Batch)\
            .filter(Batch.status == 'queued')\
            .order_by(Batch.position)\
            .first()

        if next_batch:
            next_batch.status = 'running'
            next_batch.position = self._get_running_batch_positions() + 1
            self.db.flush()  # Use self.db instead of db.session
            BatchLogService.create_log(
                next_batch.id,
                'STATE_CHANGE',
                f'Status changed to running at position {next_batch.position}'
            )
            self.reorder_queue()  # Updates positions
            self.db.commit()  # Commit both state change and queue reordering
            return next_batch

        return None

    def reorder_queue(self):
        """Reorder queue positions to be sequential after state changes
        
        This method updates queue positions but does not commit.
        The caller is responsible for committing the transaction.
        """
        # Get all queued batches
        queued_batches = self.db.query(Batch)\
            .filter(Batch.status == 'queued')\
            .order_by(Batch.position)\
            .all()

        # Get positions of running batches
        running_positions = set(
            batch.position for batch in self._get_running_batches()
        )

        # Start position after running batches
        new_position = max(running_positions) + 1 if running_positions else 1

        for batch in queued_batches:
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
        if batch.completed_profiles >= batch.total_profiles:
            self.complete_batch(batch_id)
        else:
            self.db.commit()

        return True


    def get_active_batches(self):
        """Get list of currently active (running) batches
        
        Returns:
            List[Batch]: List of active batch objects
        """
        active_batches = self.db.query(Batch)\
            .filter(Batch.status == 'running')\
            .order_by(Batch.position)\
            .all()
        return active_batches

    def get_next_batch(self):
        """Get and start the next batch to process if concurrency limits allow
        
        Returns:
            Batch: The next batch if available and under concurrency limit, None otherwise
        """
        # Check concurrency limit
        running_count = self._get_running_batch_count()
        if running_count >= self.max_concurrent_batches:
            return None

        # Get next pending batch
        next_batch = self.db.query(Batch)\
            .filter(Batch.status == 'queued')\
            .order_by(Batch.position)\
            .first()

        if next_batch:
            self.start_batch(next_batch.id)
            return next_batch

        return None

    def remove_batch(self, batch_id):
        """Remove a batch from the queue
        
        Args:
            batch_id: ID of batch to remove
            
        Returns:
            bool: True if batch removed successfully
        """
        batch = self.db.get(Batch, batch_id)
        if not batch:
            return False

        if batch.status in ('queued', 'running'):
            batch.status = 'paused'
            batch.position = None
            BatchLogService.create_log(
                batch_id,
                'STATE_CHANGE',
                'Batch removed from queue'
            )
            self.reorder_queue()
            self.db.commit()
            return True
        return False