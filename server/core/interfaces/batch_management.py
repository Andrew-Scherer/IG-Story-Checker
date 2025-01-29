"""
Batch Management Interfaces
Defines core interfaces for batch state and execution management
"""

from abc import ABC, abstractmethod
from typing import Optional
from models.batch import Batch

class IBatchStateManager(ABC):
    """Interface for managing batch state and queue positions"""
    
    @abstractmethod
    def mark_completed(self, batch_id: str) -> None:
        """Mark a batch as completed and handle queue updates
        
        Args:
            batch_id: ID of batch to mark completed
        """
        pass
    
    @abstractmethod
    def move_to_end(self, batch: Batch) -> None:
        """Move a batch to the end of the queue
        
        Args:
            batch: Batch to move
        """
        pass
    
    @abstractmethod
    def update_queue_position(self, batch: Batch, position: int) -> None:
        """Update a batch's queue position
        
        Args:
            batch: Batch to update
            position: New queue position
        """
        pass

    @abstractmethod
    def get_running_batch(self) -> Optional[Batch]:
        """Get the currently running batch
        
        Returns:
            Currently running batch or None
        """
        pass

class IBatchExecutionManager(ABC):
    """Interface for managing batch execution"""
    
    @abstractmethod
    def execute_batch(self, batch_id: str) -> None:
        """Execute a batch
        
        Args:
            batch_id: ID of batch to execute
        """
        pass
    
    @abstractmethod
    def handle_completion(self, batch_id: str) -> None:
        """Handle successful batch completion
        
        Args:
            batch_id: ID of completed batch
        """
        pass
    
    @abstractmethod
    def handle_failure(self, batch_id: str, error: str) -> None:
        """Handle batch execution failure
        
        Args:
            batch_id: ID of failed batch
            error: Error message
        """
        pass