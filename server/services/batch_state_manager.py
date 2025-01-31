"""
Batch State Manager
Single source of truth for batch state transitions and queue management
"""

from typing import Optional, List
from threading import Lock
from datetime import datetime, UTC
from flask import current_app
from models import db, Batch
from core.interfaces.batch_management import IBatchStateManager
from services.batch_log_service import BatchLogService

# Valid state transitions
VALID_TRANSITIONS = {
    'queued': {'in_progress', 'paused'},
    'in_progress': {'paused', 'done'},
    'paused': {'queued', 'in_progress'},
    'done': {'queued'}  # Allow restarting completed batches
}

class BatchStateManager(IBatchStateManager):
    """Single source of truth for batch state management"""
    
    def __init__(self):
        """Initialize BatchStateManager"""
        self._lock = Lock()
    
    def _is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """Check if state transition is valid
        
        Args:
            current_state: Current batch state
            new_state: Desired new state
            
        Returns:
            bool: True if transition is valid
        """
        return new_state in VALID_TRANSITIONS.get(current_state, set())
    
    def transition_state(self, batch: Batch, new_state: str, queue_position: Optional[int] = None) -> bool:
        """Atomic state transition with worker pool sync
        
        Args:
            batch: Batch to transition
            new_state: New state to set
            queue_position: Optional new queue position
            
        Returns:
            bool: True if transition succeeded
        """
        if not batch:
            current_app.logger.error("Batch is None in transition_state")
            return False

        with self._lock:
            try:
                # Get fresh instance
                fresh_batch = db.session.get(Batch, batch.id)
                if not fresh_batch:
                    current_app.logger.error(f"Batch {batch.id} not found in transition_state")
                    return False
                    
                # Validate transition
                if not self._is_valid_transition(fresh_batch.status, new_state):
                    current_app.logger.error(
                        f"Invalid state transition from {fresh_batch.status} to {new_state}"
                    )
                    return False
                
                # Update state and position atomically
                old_state = fresh_batch.status
                fresh_batch.status = new_state
                
                if queue_position is not None:
                    fresh_batch.queue_position = queue_position
                
                # Handle worker pool operations
                if new_state == 'in_progress':
                    current_app.worker_pool.register_batch(fresh_batch.id)
                elif old_state == 'in_progress':
                    current_app.worker_pool.unregister_batch(fresh_batch.id)
                
                # Set completed_at when transitioning to done
                if new_state == 'done':
                    fresh_batch.completed_at = datetime.now(UTC)
                
                # Log the transition
                position_msg = f" at position {queue_position}" if queue_position is not None else ""
                BatchLogService.create_log(
                    fresh_batch.id,
                    'STATE_CHANGE',
                    f'Status changed from {old_state} to {new_state}{position_msg}'
                )
                
                db.session.flush()
                return True
                    
            except Exception as e:
                current_app.logger.error(f"Error in transition_state: {str(e)}")
                db.session.rollback()
                return False
    
    def get_next_position(self) -> int:
        """Get next available queue position
        
        Returns:
            int: Next available position
        """
        with self._lock:
            last_position = db.session.query(db.func.max(Batch.queue_position))\
                .filter(Batch.queue_position.isnot(None)).scalar()
            return (last_position or 0) + 1
    
    def reorder_queue(self) -> None:
        """Reorder remaining queued batches to ensure sequential positions"""
        with self._lock:
            try:
                # Get queued batches in current order
                queued_batches = Batch.query.filter(Batch.queue_position > 0)\
                    .order_by(Batch.queue_position).all()
                
                if not queued_batches:
                    return
                
                # Reorder sequentially
                for i, batch in enumerate(queued_batches, 1):
                    if batch.queue_position != i:
                        batch.queue_position = i
                        BatchLogService.create_log(
                            batch.id,
                            'QUEUE_UPDATE',
                            f'Reordered to position {i}'
                        )
                
                db.session.flush()
                
            except Exception as e:
                current_app.logger.error(f"Error reordering queue: {str(e)}")
                db.session.rollback()
    
    def mark_completed(self, batch_id: str) -> None:
        """Mark a batch as completed
        
        Args:
            batch_id: ID of batch to mark completed
        """
        batch = db.session.get(Batch, batch_id)
        if batch:
            if self.transition_state(batch, 'done', None):
                self.reorder_queue()
    
    def move_to_end(self, batch: Batch) -> None:
        """Move batch to end of queue and reset its progress
        
        Args:
            batch: Batch to move
        """
        if not batch:
            return
            
        with self._lock:
            try:
                # Get fresh instance
                fresh_batch = db.session.get(Batch, batch.id)
                if not fresh_batch:
                    current_app.logger.error(f"Batch {batch.id} not found in move_to_end")
                    return
                
                # Reset batch progress
                fresh_batch.completed_profiles = 0
                fresh_batch.successful_checks = 0
                fresh_batch.failed_checks = 0
                
                # Reset all batch profiles
                for batch_profile in fresh_batch.profiles:
                    batch_profile.status = 'pending'
                    batch_profile.has_story = False
                    batch_profile.error = None
                    batch_profile.processed_at = None
                
                # Move to end of queue
                next_pos = self.get_next_position()
                self.transition_state(fresh_batch, 'queued', next_pos)
                
                db.session.flush()
                
            except Exception as e:
                current_app.logger.error(f"Error in move_to_end: {str(e)}")
                db.session.rollback()
    
    def get_running_batch(self) -> Optional[Batch]:
        """Get currently running batch
        
        Returns:
            Currently running batch or None
        """
        return Batch.query.filter_by(queue_position=0).first()

    def update_queue_position(self, batch: Batch, position: int) -> None:
        """Update a batch's queue position
        
        Args:
            batch: Batch to update
            position: New queue position
        """
        if not batch:
            return
            
        with self._lock:
            try:
                # Get fresh instance
                fresh_batch = db.session.get(Batch, batch.id)
                if not fresh_batch:
                    current_app.logger.error(f"Batch {batch.id} not found in update_queue_position")
                    return
                
                old_pos = fresh_batch.queue_position
                fresh_batch.queue_position = position
                
                BatchLogService.create_log(
                    fresh_batch.id,
                    'QUEUE_UPDATE',
                    f'Updated queue position from {old_pos} to {position}'
                )
                
                db.session.flush()
                    
            except Exception as e:
                current_app.logger.error(f"Error updating queue position: {str(e)}")
                db.session.rollback()