"""
Batch Execution Manager
Handles batch execution logic and processing
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Optional
from flask import current_app
from models import db, Batch, BatchProfile
from core.interfaces.batch_management import IBatchStateManager, IBatchExecutionManager
from core.worker import WorkerPool
from services.batch_log_service import BatchLogService

from threading import Lock

class BatchExecutionManager(IBatchExecutionManager):
    """Manages batch execution and processing"""

    def __init__(self, state_manager: IBatchStateManager):
        """Initialize BatchExecutionManager
        
        Args:
            state_manager: State manager implementation
        """
        self.state_manager = state_manager
        self._executing_batches = set()
        self._lock = Lock()

    def is_executing(self, batch_id: str) -> bool:
        """Check if batch is currently executing"""
        with self._lock:
            return batch_id in self._executing_batches

    def start_execution(self, batch_id: str) -> bool:
        """Try to start batch execution"""
        with self._lock:
            if batch_id in self._executing_batches:
                return False
            self._executing_batches.add(batch_id)
            return True

    def stop_execution(self, batch_id: str) -> None:
        """Stop batch execution"""
        with self._lock:
            self._executing_batches.discard(batch_id)

    def process_batch(self, batch_id: str) -> None:
        """Process a single batch
        
        Args:
            batch_id: ID of batch to process
        """
        current_app.logger.info(f"=== Processing Batch {batch_id} ===")
        self.execute_batch(batch_id)

    async def _process_batch_async(self, batch_id: str, worker_pool: WorkerPool) -> None:
        """Process a single batch asynchronously
        
        Args:
            batch_id: ID of batch to process
            worker_pool: Worker pool to use
        """
        batch = None
        try:
            batch = db.session.get(Batch, batch_id)
            if not batch:
                current_app.logger.error(f'Batch {batch_id} not found')
                BatchLogService.create_log(batch_id, 'ERROR', f'Batch {batch_id} not found')
                return

            # Get profiles that need processing
            remaining_profiles = [
                bp for bp in batch.profiles
                if bp.status not in ['completed', 'failed']
            ]
            current_app.logger.info(f"Processing {len(remaining_profiles)} profiles")
            BatchLogService.create_log(
                batch_id,
                'INFO',
                f'Processing {len(remaining_profiles)} profiles'
            )
            
            for batch_profile in remaining_profiles:
                BatchLogService.create_log(
                    batch_id, 
                    'PROFILE_CHECK_START',
                    f'Starting check for {batch_profile.profile.username}',
                    profile_id=batch_profile.profile.id
                )

                # Get available worker with retries
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
                    batch_profile.status = 'failed'
                    batch_profile.error = 'No worker available after retries'
                    batch.failed_checks += 1
                    batch.completed_profiles += 1
                    db.session.commit()
                    continue

                try:
                    # Check story
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
                    batch_profile.status = 'failed'
                    batch_profile.error = str(e)
                    batch.failed_checks += 1
                    BatchLogService.create_log(
                        batch_id,
                        'CHECK_FAILED',
                        f'Check failed for {batch_profile.profile.username}: {str(e)}',
                        profile_id=batch_profile.profile.id
                    )

                finally:
                    await worker_pool.release_worker(worker)
                    await asyncio.sleep(1)

                # Update completed_profiles count
                batch.completed_profiles = len([
                    bp for bp in batch.profiles
                    if bp.status in ['completed', 'failed']
                ])
                db.session.commit()

            # Check if all profiles are processed
            all_profiles_count = len(batch.profiles)
            completed_count = len([bp for bp in batch.profiles if bp.status in ['completed', 'failed']])
            
            if completed_count >= all_profiles_count:
                self.state_manager.mark_completed(batch_id)
            
            BatchLogService.create_log(
                batch_id,
                'BATCH_END',
                f'Batch completed: {batch.successful_checks} successful, {batch.failed_checks} failed'
            )

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
        if not self.start_execution(batch_id):
            current_app.logger.error(f"Batch {batch_id} is already executing")
            return

        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Get worker pool
            worker_pool = getattr(current_app, 'worker_pool', None)
            if not worker_pool:
                current_app.logger.error('No worker pool available')
                BatchLogService.create_log(batch_id, 'ERROR', 'No worker pool available')
                return

            # Run the async process_batch function
            loop.run_until_complete(self._process_batch_async(batch_id, worker_pool))

        except Exception as e:
            current_app.logger.error(f'Error in execute_batch: {e}', exc_info=True)
            BatchLogService.create_log(batch_id, 'ERROR', f'Error in execute_batch: {str(e)}')
            self.handle_failure(batch_id, str(e))
            raise

        finally:
            self.stop_execution(batch_id)
            loop.close()

    def handle_completion(self, batch_id: str) -> None:
        """Handle successful batch completion
        
        Args:
            batch_id: ID of completed batch
        """
        self.state_manager.mark_completed(batch_id)

    def handle_failure(self, batch_id: str, error: str) -> None:
        """Handle batch execution failure
        
        Args:
            batch_id: ID of failed batch
            error: Error message
        """
        batch = db.session.get(Batch, batch_id)
        if batch:
            self.state_manager.move_to_end(batch)