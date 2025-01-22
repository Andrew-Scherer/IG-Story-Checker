"""
Queue Ordering Service
Handles reordering of batches in the queue
"""

from flask import current_app
from models import db, Batch
from services.batch_log_service import BatchLogService
from config.logging_config import setup_component_logging

logger = setup_component_logging('queue_ordering')

def reorder_queue():
    """Reorder remaining queued batches to ensure sequential positions"""
    logger.info("reorder_queue function called")
    logger.info("=== Reordering Queue ===")
    queued_batches = Batch.query.filter(Batch.queue_position > 0)\
        .order_by(Batch.queue_position).all()
    logger.info(f"1. Found {len(queued_batches)} queued batches")

    if not queued_batches:
        logger.info("No queued batches found. Queue reorder not necessary.")
        return

    logger.info("Current queue order:")
    for batch in queued_batches:
        logger.info(f"Batch {batch.id}: position {batch.queue_position}")

    for i, batch in enumerate(queued_batches):
        new_position = i + 1
        old_pos = batch.queue_position
        if old_pos != new_position:
            logger.info(f"2. Moving batch {batch.id} from position {old_pos} to {new_position}")
            batch.queue_position = new_position
            BatchLogService.create_log(
                batch.id,
                'INFO',
                f'Reordered from position {old_pos} to {new_position}'
            )
        else:
            logger.info(f"2. Batch {batch.id} already in correct position {new_position}")

    db.session.commit()
    logger.info("3. Queue reorder complete")

    logger.info("New queue order:")
    for batch in queued_batches:
        logger.info(f"Batch {batch.id}: position {batch.queue_position}")
