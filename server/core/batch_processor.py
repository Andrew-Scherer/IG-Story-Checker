"""
Batch Processor
Provides backward compatibility layer for batch processing
"""

from flask import current_app
from services.queue_manager import queue_manager

def process_batch(batch_id: str):
    """Process a single batch
    
    This function maintains backward compatibility with existing code
    while delegating to the new implementation.
    
    Args:
        batch_id: ID of batch to process
    """
    current_app.logger.info(f"=== Delegating batch {batch_id} to execution manager ===")
    queue_manager.execution_manager.execute_batch(batch_id)
