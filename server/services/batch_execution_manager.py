"""
Batch Execution Manager
Handles batch processing and execution logic
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Optional
from flask import current_app
from models import db, Batch
from core.interfaces.batch_management import IBatchStateManager, IBatchExecutionManager
from core.worker import WorkerPool
from services.batch_log_service import BatchLogService

class BatchExecutionManager(IBatchExecutionManager):
    """Manages batch execution and processing"""

    def __init__(self, state_manager: IBatchStateManager):
        """Initialize BatchExecutionManager
        
        Args:
            state_manager: State manager implementation
        """
        self.state_manager = state_manager

    async def _process_batch_async(self, batch_id: str, worker_pool: WorkerPool) -> None:
        """Process a single batch asynchronously
        
        Args:
            batch_id: ID of batch to process
            worker_pool: Worker pool to use
        """
        batch = None
        try:
            # Log batch lookup
            current_app.logger.info(f"=== Starting Batch {batch_id} ===")
            current_app.logger.info("1. Looking up batch in database...")
            batch = db.session.get(Batch, batch_id)
            if not batch:
                current_app.logger.error(f'Batch {batch_id} not found')
                BatchLogService.create_log(batch_id, 'ERROR', f'Batch {batch_id} not found')
                return

            # Log batch start
            current_app.logger.info(f"2. Found batch with {batch.total_profiles} profiles")
            BatchLogService.create_log(batch_id, 'BATCH_START', f'Starting batch processing for {batch.total_profiles} profiles')

            # Mark as in_progress
            current_app.logger.info("3. Updating batch status to in_progress...")
            batch.status = 'in_progress'
            batch.completed_profiles = 0
            batch.successful_checks = 0
            batch.failed_checks = 0
            db.session.commit()
            BatchLogService.create_log(batch_id, 'STATUS_UPDATE', f'Batch status updated to in_progress')

            # Process each profile
            current_app.logger.info("4. Beginning profile processing...")
            db.session.refresh(batch)
            for batch_profile in batch.profiles:
                BatchLogService.create_log(
                    batch_id, 
                    'PROFILE_CHECK_START',
                    f'Starting check for profile {batch_profile.profile.username}',
                    profile_id=batch_profile.profile.id
                )

                # Get available worker with retries
                current_app.logger.info("5. Requesting worker from pool...")
                MAX_WORKER_RETRIES = 5
                worker = None
                retry_count = 0

                while not worker and retry_count < MAX_WORKER_RETRIES:
                    worker = worker_pool.get_worker()
                    if not worker:
                        retry_count += 1
                        wait_time = 20  # Same as proxy cooldown
                        current_app.logger.info(f'No workers available, waiting {wait_time}s before retry {retry_count}/{MAX_WORKER_RETRIES}...')
                        BatchLogService.create_log(
                            batch_id,
                            'WORKER_WAIT',
                            f'No workers available, waiting {wait_time}s before retry {retry_count}/{MAX_WORKER_RETRIES}...'
                        )
                        await asyncio.sleep(wait_time)

                if not worker:
                    current_app.logger.error('Failed to get worker after max retries')
                    BatchLogService.create_log(
                        batch_id,
                        'WORKER_UNAVAILABLE',
                        'Failed to get worker after max retries'
                    )
                    batch_profile.status = 'failed'
                    batch_profile.error = 'No worker available after retries'
                    batch.failed_checks += 1
                    batch.completed_profiles += 1
                    db.session.commit()
                    continue

                current_app.logger.info(f'6. Got worker with proxy {worker.proxy_session.proxy_url_safe}')
                BatchLogService.create_log(
                    batch_id,
                    'WORKER_ASSIGNED',
                    f'Worker assigned with proxy {worker.proxy_session.proxy_url_safe}',
                    proxy_id=worker.proxy_session.proxy.id
                )

                try:
                    # Check story
                    current_app.logger.info(f'7. Checking story for {batch_profile.profile.username}')
                    BatchLogService.create_log(
                        batch_id,
                        'STORY_CHECK_START',
                        f'Checking story for {batch_profile.profile.username}',
                        profile_id=batch_profile.profile.id,
                        proxy_id=worker.proxy_session.proxy.id
                    )

                    # Try to check story with retries for rate limits
                    MAX_RETRIES = 3
                    retry_count = 0
                    success = False
                    has_story = False
                    while retry_count < MAX_RETRIES and not success:
                        try:
                            start_time = time.time()
                            success, has_story = await worker.check_story(batch_profile)
                            end_time = time.time()
                            duration = end_time - start_time

                            if success:
                                batch_profile.status = 'completed'
                                batch_profile.has_story = has_story
                                batch_profile.error = None
                                if has_story:
                                    batch.successful_checks += 1
                                    batch_profile.profile.record_check(story_detected=True)
                                BatchLogService.create_log(
                                    batch_id,
                                    'STORY_CHECK_SUCCESS',
                                    f'Story check succeeded for {batch_profile.profile.username}. Story detected: {has_story}. Duration: {duration:.2f} seconds',
                                    profile_id=batch_profile.profile.id
                                )
                                BatchLogService.create_log(
                                    batch_id,
                                    'STORY_STATUS',
                                    'Story found!' if has_story else 'Story not found!',
                                    profile_id=batch_profile.profile.id
                                )
                            else:
                                error_msg = getattr(batch_profile, 'error', 'Unknown error')
                                BatchLogService.create_log(
                                    batch_id,
                                    'CHECK_FAILED',
                                    f'Check failed for {batch_profile.profile.username}: {error_msg}. Duration: {duration:.2f} seconds',
                                    profile_id=batch_profile.profile.id
                                )
                                batch.failed_checks += 1

                        except Exception as e:
                            if "Rate limited" in str(e):
                                retry_count += 1
                                if retry_count < MAX_RETRIES:
                                    current_app.logger.info(f'Rate limited, waiting before retry {retry_count} for {batch_profile.profile.username}')
                                    await asyncio.sleep(20)
                                    continue

                            batch_profile.status = 'failed'
                            batch_profile.error = str(e)
                            batch.failed_checks += 1
                            BatchLogService.create_log(
                                batch_id,
                                'CHECK_FAILED',
                                f'Check failed for {batch_profile.profile.username}: {str(e)}',
                                profile_id=batch_profile.profile.id
                            )
                            break

                    BatchLogService.create_log(
                        batch_id,
                        'PROFILE_CHECK_END',
                        f'Check complete for profile {batch_profile.profile.username}',
                        profile_id=batch_profile.profile.id
                    )

                    await asyncio.sleep(20)  # Delay between profiles

                finally:
                    current_app.logger.info(f'8. Releasing worker with proxy {worker.proxy_session.proxy_url_safe}')
                    await worker_pool.release_worker(worker)
                    await asyncio.sleep(1)

                batch.completed_profiles += 1
                db.session.commit()

            # Complete batch
            current_app.logger.info("9. Batch processing complete")
            batch.completed_at = datetime.now(UTC)
            db.session.commit()

            current_app.logger.info(f'Batch {batch.id} completed: {batch.successful_checks} successful, {batch.failed_checks} failed')
            BatchLogService.create_log(
                batch_id,
                'BATCH_END',
                f'Batch completed: {batch.successful_checks} successful, {batch.failed_checks} failed'
            )

            # Handle completion through state manager
            self.handle_completion(batch_id)

        except Exception as e:
            current_app.logger.error(f'Error processing batch {batch_id}: {e}', exc_info=True)
            BatchLogService.create_log(batch_id, 'BATCH_ERROR', f'Error processing batch: {str(e)}')
            if batch:
                self.handle_failure(batch_id, str(e))

    def execute_batch(self, batch_id: str) -> None:
        """Execute a batch
        
        Args:
            batch_id: ID of batch to execute
        """
        current_app.logger.info(f"=== Starting execute_batch for batch_id: {batch_id} ===")

        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Get worker pool
            current_app.logger.info("1. Getting worker pool...")
            worker_pool = getattr(current_app, 'worker_pool', None)
            current_app.logger.info(f"2. Worker pool obtained: {worker_pool is not None}")
            if not worker_pool:
                current_app.logger.error('No worker pool available')
                BatchLogService.create_log(batch_id, 'ERROR', 'No worker pool available')
                return

            # Verify batch exists
            current_app.logger.info("3. Verifying batch exists...")
            batch = db.session.get(Batch, batch_id)
            if not batch:
                current_app.logger.error(f'Batch {batch_id} not found')
                BatchLogService.create_log(batch_id, 'ERROR', f'Batch {batch_id} not found')
                return

            # Run the async process_batch function
            current_app.logger.info(f"4. Running process_batch_async for batch_id: {batch_id}")
            loop.run_until_complete(self._process_batch_async(batch_id, worker_pool))

        except Exception as e:
            current_app.logger.error(f'Error in execute_batch: {e}', exc_info=True)
            BatchLogService.create_log(batch_id, 'ERROR', f'Error in execute_batch: {str(e)}')
            self.handle_failure(batch_id, str(e))
            raise

        finally:
            loop.close()
            current_app.logger.info(f"=== Finished execute_batch for batch_id: {batch_id} ===")
            BatchLogService.create_log(batch_id, 'INFO', f'Finished execute_batch for batch_id: {batch_id}')

    def handle_completion(self, batch_id: str) -> None:
        """Handle successful batch completion
        
        Args:
            batch_id: ID of completed batch
        """
        current_app.logger.info(f"Handling completion for batch {batch_id}")
        self.state_manager.mark_completed(batch_id)
        worker_pool = getattr(current_app, 'worker_pool', None)
        if worker_pool:
            worker_pool.unregister_batch(batch_id)
            current_app.logger.info(f'Unregistered batch {batch_id} from worker pool')

    def handle_failure(self, batch_id: str, error: str) -> None:
        """Handle batch execution failure
        
        Args:
            batch_id: ID of failed batch
            error: Error message
        """
        current_app.logger.info(f"Handling failure for batch {batch_id}: {error}")
        batch = db.session.get(Batch, batch_id)
        if batch:
            self.state_manager.move_to_end(batch)
            worker_pool = getattr(current_app, 'worker_pool', None)
            if worker_pool:
                worker_pool.unregister_batch(batch_id)
                current_app.logger.info(f'Unregistered batch {batch_id} from worker pool')