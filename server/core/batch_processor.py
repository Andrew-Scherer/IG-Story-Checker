"""
Batch Processor
Handles batch processing and story checking
"""

import asyncio
from datetime import datetime, UTC
from typing import Optional
from flask import current_app
from models import db, Batch
from server.core.worker.pool import WorkerPool
from server.models.proxy import Proxy
from server.models.session import Session
from server.services.batch_manager import BatchManager
from server.services.batch_log_service import BatchLogService

class BatchProcessor:
    """Handles batch processing with worker pool management"""

    def __init__(self, db_session, worker_pool: Optional[WorkerPool] = None):
        """Initialize batch processor
        
        Args:
            db_session: Database session
            worker_pool: Optional WorkerPool instance. If not provided, a new one will be created.
        """
        self.db = db_session
        self.batch_manager = BatchManager(db_session)
        self.worker_pool = worker_pool or WorkerPool(5)  # Use provided pool or create new one

    async def _process_batch_async(self, batch_id: str, worker_pool: WorkerPool) -> None:
        """Process a single batch asynchronously
        
        Args:
            batch_id: ID of batch to process
            worker_pool: Worker pool to use
        """
        try:
            current_app.logger.info(f'=== Processing Batch {batch_id} ===')
            batch = self.db.get(Batch, batch_id)
            if not batch:
                current_app.logger.error(f'Batch {batch_id} not found')
                return

            # Add available proxies to pool
            current_app.logger.info('1. Adding proxies to worker pool...')
            proxies = Proxy.query.filter_by(is_active=True).all()
            worker_pool.add_proxies(proxies)

            # Process each profile
            current_app.logger.info('2. Processing profiles...')
            for batch_profile in batch.profiles:
                if batch_profile.status == 'completed':
                    continue

                # Get worker with retries
                current_app.logger.info('3. Getting worker...')
                retries = 3
                worker = None
                
                for attempt in range(retries):
                    worker = worker_pool.get_worker()
                    if worker:
                        current_app.logger.info(f'Successfully got worker on attempt {attempt + 1}')
                        break
                    current_app.logger.warning(f'No worker available on attempt {attempt + 1}/{retries}')
                    await asyncio.sleep(1)  # Wait before retry
                
                if not worker:
                    warning_msg = (
                        'No workers available after retries. Possible reasons:\n'
                        '- No active proxies in database\n'
                        '- Proxies exist but failed to register with session manager\n'
                        '- All workers are currently in use'
                    )
                    current_app.logger.warning(warning_msg)  # Change from error to warning
                    
                    # Log detailed state for debugging
                    proxies = Proxy.query.filter_by(is_active=True).all()
                    current_app.logger.warning(f'Active proxies in DB: {len(proxies)}')
                    for proxy in proxies:
                        current_app.logger.warning(
                            f'Proxy {proxy.ip}:{proxy.port} - '
                            f'Active: {proxy.is_active}, '
                            f'Status: {proxy.status}, '
                            f'Sessions: {len(proxy.sessions)}'
                        )

                    BatchLogService.create_log(batch_id, 'BATCH_PAUSED', warning_msg)  # Change log type
                    
                    batch.status = 'paused'  # Correct status for no workers
                    batch.position = None  # Reset position when pausing
                    batch.error = warning_msg
                    self.db.commit()
                    return

                try:
                    # Check story
                    current_app.logger.info(f'4. Checking story for {batch_profile.profile.username}...')
                    success, has_story = await worker.check_story(batch_profile)

                    if success:
                        current_app.logger.info('5. Story check successful')
                        batch_profile.status = 'completed'
                        batch_profile.has_story = has_story
                        batch_profile.processed_at = datetime.now(UTC)
                        batch.successful_checks += 1
                        BatchLogService.create_log(
                            batch_id,
                            'PROFILE_CHECK',
                            f'Successfully checked {batch_profile.profile.username} (has_story={has_story})'
                        )
                    else:
                        current_app.logger.warning('6. Story check failed')
                        batch_profile.status = 'failed'
                        batch.failed_checks += 1
                        self.db.commit()  # Commit the failed_checks increment
                        BatchLogService.create_log(
                            batch_id,
                            'PROFILE_ERROR',
                            f'Failed to check {batch_profile.profile.username}'
                        )

                    # Update progress
                    current_app.logger.info('7. Updating batch progress...')
                    completed = sum(1 for p in batch.profiles if p.status == 'completed')
                    successful = sum(1 for p in batch.profiles if p.has_story)
                    failed = sum(1 for p in batch.profiles if p.status == 'failed')
                    self.batch_manager.update_progress(
                        batch_id,
                        completed=completed,
                        successful=successful,
                        failed=failed
                    )

                finally:
                    # Release worker
                    current_app.logger.info('8. Releasing worker...')
                    await worker_pool.release_worker(worker)

            # Check if batch is complete
            # Check if batch is complete
            if all(p.status in ('completed', 'failed') for p in batch.profiles):
                current_app.logger.info('9. Batch complete, marking as done')
                batch.status = 'done'
                batch.position = None
                batch.completed_at = datetime.now(UTC)
                self.db.commit()
                self.batch_manager.complete_batch(batch_id)

        except Exception as e:
            current_app.logger.error(f'Error processing batch: {str(e)}')
            batch.failed_checks += 1
            batch.status = 'error'
            self.db.commit()
            BatchLogService.create_log(batch_id, 'BATCH_ERROR', f'Error processing batch: {str(e)}')
            self.batch_manager.handle_error(batch_id, str(e))

async def process_batches(db_session=None, worker_pool: Optional[WorkerPool] = None):
    """Process pending batches
    
    Args:
        db_session: Optional database session. If not provided, uses flask app session.
        worker_pool: Optional WorkerPool instance. If not provided, creates a new one.
    """
    try:
        # Use provided session or get from flask app
        session = db_session if db_session is not None else db.session

        # Get running batch
        batch_manager = BatchManager(session)
        running_batch = session.query(Batch).filter(Batch.position == 0).first()
        
        if not running_batch:
            # Try to promote next batch
            next_batch = batch_manager.promote_next_batch()
            if not next_batch:
                return
            running_batch = next_batch
            session.refresh(running_batch)  # Refresh to get latest state

        # Process the batch using provided or new worker pool
        worker_pool = worker_pool or WorkerPool(5)  # Use provided pool or create new one
        processor = BatchProcessor(session, worker_pool)  # Pass worker_pool to processor
        await processor._process_batch_async(running_batch.id, worker_pool)

        # Ensure batch is marked as done
        batch = session.get(Batch, running_batch.id)
        if batch:
            session.refresh(batch)  # Refresh to get latest state
            session.refresh(batch)  # Refresh to get latest state
            if batch.status in ('queued', 'running'):  # Check both queued and running states
                if all(p.status in ('completed', 'failed') for p in batch.profiles):
                    current_app.logger.info(f'Marking batch {batch.id} as done')
                    batch.status = 'done'
                    batch.position = None
                    batch.completed_at = datetime.now(UTC)
                    session.commit()
                    current_app.logger.info(f'Batch {batch.id} marked as done')

    except Exception as e:
        current_app.logger.error(f'Error in process_batches: {str(e)}')
        if running_batch:
            batch_manager.handle_error(running_batch.id, str(e))
