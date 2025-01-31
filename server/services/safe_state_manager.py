"""
Safe State Manager
Provides safe state transitions and non-blocking error logging
"""

from flask import current_app
from models import db, Batch
from services.batch_log_service import BatchLogService

def safe_log_error(batch_id: str, error_msg: str) -> None:
    """Log error without blocking on failure
    
    Args:
        batch_id: ID of batch to log error for
        error_msg: Error message to log
    """
    try:
        BatchLogService.create_log(batch_id, 'ERROR', error_msg)
    except Exception as e:
        # Just log to app logger if batch logging fails
        current_app.logger.error(f"Failed to log error for batch {batch_id}: {str(e)}")
        current_app.logger.error(f"Original error was: {error_msg}")

def transition_batch_state(batch: Batch, new_status: str, reason: str = None) -> bool:
    """Atomic batch state transition
    
    Args:
        batch: Batch to transition
        new_status: New status to set
        reason: Optional reason for transition
    
    Returns:
        bool: True if transition succeeded, False otherwise
    """
    try:
        # Use nested transaction to ensure atomicity
        with db.session.begin_nested():
            # Get fresh instance
            batch = db.session.get(Batch, batch.id)
            if not batch:
                current_app.logger.error(f"Batch {batch.id} not found in transition_batch_state")
                return False
            
            old_status = batch.status
            batch.status = new_status
            
            # Try to log the transition
            try:
                BatchLogService.create_log(
                    batch.id,
                    'STATE_CHANGE',
                    f'Status changed from {old_status} to {new_status}' + (f': {reason}' if reason else '')
                )
            except Exception as e:
                current_app.logger.error(f"Failed to log state change for batch {batch.id}: {str(e)}")
            
            db.session.commit()
            return True
            
    except Exception as e:
        current_app.logger.error(f"Error transitioning batch {batch.id} state: {str(e)}")
        db.session.rollback()
        return False

def sync_worker_pool(worker_pool) -> None:
    """Sync worker pool with database state
    
    Args:
        worker_pool: Worker pool to sync
    """
    try:
        # Get currently running batch from database
        running_batch = Batch.query.filter_by(queue_position=0).first()
        
        with worker_pool._lock:
            # Clear running batches if none running in database
            if not running_batch:
                worker_pool.running_batches.clear()
                current_app.logger.info("Cleared worker pool running batches - none running in database")
                return
            
            # Sync running batch
            batch_id = running_batch.id
            if batch_id not in worker_pool.running_batches:
                # Batch is running in DB but not in worker pool
                if running_batch.status != 'in_progress':
                    # Reset inconsistent state
                    running_batch.status = 'queued'
                    running_batch.queue_position = None
                    db.session.commit()
                    current_app.logger.info(f"Reset inconsistent batch {batch_id}")
                else:
                    # Add to worker pool
                    worker_pool.running_batches.add(batch_id)
                    current_app.logger.info(f"Added missing batch {batch_id} to worker pool")
            
            # Remove any batches that aren't actually running
            for batch_id in list(worker_pool.running_batches):
                batch = Batch.query.get(batch_id)
                if not batch or batch.queue_position != 0:
                    worker_pool.running_batches.remove(batch_id)
                    current_app.logger.info(f"Removed non-running batch {batch_id} from worker pool")
                    
    except Exception as e:
        current_app.logger.error(f"Error syncing worker pool: {str(e)}")