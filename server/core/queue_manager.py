"""
Queue Manager
Manages batch processing queue and concurrency
"""

from typing import Optional, List, Set
from datetime import datetime, UTC
from models.batch import Batch

from sqlalchemy.orm import Session

class QueueManager:
    """Manages batch processing queue and enforces concurrency limits"""
    
    def __init__(self, max_concurrent_batches: int = 2):
        """Initialize queue manager
        
        Args:
            max_concurrent_batches: Maximum number of batches that can run concurrently
        """
        self.max_concurrent_batches = max_concurrent_batches
        self._pending_batches: List[str] = []  # List of batch IDs
        self._active_batches: Set[str] = set()  # Set of active batch IDs
        self._session: Optional[Session] = None
    
    def add_batch(self, batch: Batch, session: Session) -> None:
        """Add a batch to the processing queue
        
        Args:
            batch: The batch to add
        """
        if batch.id not in self._pending_batches and batch.id not in self._active_batches:
            self._pending_batches.append(batch.id)
    
    def peek_next_batch(self, session: Session) -> Optional[Batch]:
        """Get the next batch without starting it
        
        Returns:
            The next available batch without changing its state, None if no batch available
        """
        # Check concurrent batch limit
        if len(self._active_batches) >= self.max_concurrent_batches:
            return None
            
        # Find next valid batch
        for batch_id in self._pending_batches:
            batch = session.get(Batch, batch_id)
            if batch and batch.status not in ('completed', 'failed'):
                return batch
                
        return None
    
    def get_next_batch(self, session: Session) -> Optional[Batch]:
        """Get and start the next batch to process
        
        Returns:
            The next batch if available and under concurrent limit, None otherwise
        """
        # Check concurrent batch limit
        if len(self._active_batches) >= self.max_concurrent_batches:
            return None
            
        # Get next pending batch
        while self._pending_batches:
            batch_id = self._pending_batches[0]
            batch = session.get(Batch, batch_id)
            
            # Skip if batch no longer exists or is already complete/failed
            if not batch or batch.status in ('completed', 'failed'):
                self._pending_batches.pop(0)
                continue
                
            # Start the batch
            self._pending_batches.pop(0)
            self._active_batches.add(batch.id)
            batch.start(session=session)
            return batch
            
        return None
    
    def remove_batch(self, batch_id: str) -> None:
        """Remove a batch from the queue
        
        Args:
            batch_id: ID of batch to remove
        """
        if batch_id in self._pending_batches:
            self._pending_batches.remove(batch_id)
        if batch_id in self._active_batches:
            self._active_batches.remove(batch_id)
    
    def get_active_batches(self, session: Session) -> List[Batch]:
        """Get list of currently active batches
        
        Returns:
            List of active batch objects
        """
        active_batches = []
        for batch_id in list(self._active_batches):
            batch = session.get(Batch, batch_id)
            if not batch or batch.status in ('completed', 'failed'):
                self._active_batches.remove(batch_id)
            else:
                active_batches.append(batch)
        return active_batches
    
    def clear(self) -> None:
        """Clear all batches from queue"""
        self._pending_batches.clear()
        self._active_batches.clear()
