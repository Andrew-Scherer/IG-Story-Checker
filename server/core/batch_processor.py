# Batch Processor
# Handles background processing of batches

import asyncio
import time
from datetime import datetime, UTC
from models import db, Batch, BatchProfile, Profile
from core.worker import WorkerPool
from flask import current_app
from services.batch_log_service import BatchLogService
from services.queue_manager import QueueManager
from config.logging_config import setup_component_logging

# Set up dedicated logger for batch processor
logger = setup_component_logging('batch_processor')

async def process_batch_async(batch_id: str, worker_pool: WorkerPool):
    """Process a single batch asynchronously

    Args:
        batch_id: ID of batch to process
        worker_pool: Worker pool to use
    """
    # Get app reference before entering context
    from flask import current_app as app

    batch = None
    try:
        with app.app_context():
            # Log batch lookup
            logger.info(f"=== Starting Batch {batch_id} ===")
            logger.info("1. Looking up batch in database...")
            batch = db.session.get(Batch, batch_id)
            if not batch:
                logger.error(f'Batch {batch_id} not found')
                BatchLogService.create_log(batch_id, 'ERROR', f'Batch {batch_id} not found')
                return

            # Log batch start
            logger.info(f"2. Found batch with {batch.total_profiles} profiles")
            BatchLogService.create_log(batch_id, 'BATCH_START', f'Starting batch processing for {batch.total_profiles} profiles')

            # Now that we've confirmed we can start, mark as in_progress
            logger.info("3. Updating batch status to in_progress...")
            batch.status = 'in_progress'
            batch.completed_profiles = 0
            batch.successful_checks = 0
            batch.failed_checks = 0
            db.session.commit()
            BatchLogService.create_log(batch_id, 'STATUS_UPDATE', f'Batch status updated to in_progress')

            # Process each profile
            logger.info("4. Beginning profile processing...")
            # Refresh the batch to ensure it's associated with the current session
            db.session.refresh(batch)
            for batch_profile in batch.profiles:
                BatchLogService.create_log(
                    batch_id, 
                    'PROFILE_CHECK_START',
                    f'Starting check for profile {batch_profile.profile.username}',
                    profile_id=batch_profile.profile.id
                )

                # Get available worker with retries
                logger.info("5. Requesting worker from pool...")
                MAX_WORKER_RETRIES = 5
                worker = None
                retry_count = 0

                while not worker and retry_count < MAX_WORKER_RETRIES:
                    worker = worker_pool.get_worker()
                    if not worker:
                        retry_count += 1
                        wait_time = 20  # Same as our proxy cooldown
                        logger.info(f'No workers available, waiting {wait_time}s before retry {retry_count}/{MAX_WORKER_RETRIES}...')
                        BatchLogService.create_log(
                            batch_id,
                            'WORKER_WAIT',
                            f'No workers available, waiting {wait_time}s before retry {retry_count}/{MAX_WORKER_RETRIES}...'
                        )
                        await asyncio.sleep(wait_time)

                if not worker:
                    logger.error('Failed to get worker after max retries')
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

                logger.info(f'6. Got worker with proxy {worker.proxy_session.proxy_url_safe}')
                BatchLogService.create_log(
                    batch_id,
                    'WORKER_ASSIGNED',
                    f'Worker assigned with proxy {worker.proxy_session.proxy_url_safe}',
                    proxy_id=worker.proxy_session.proxy.id
                )

                try:
                    # Check story
                    logger.info(f'7. Checking story for {batch_profile.profile.username}')
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
                                # Only log success after verification
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
                                # Log failed check with error details
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
                                    logger.info(f'Rate limited, waiting before retry {retry_count} for {batch_profile.profile.username}')
                                    await asyncio.sleep(20)  # Wait 20 seconds between retries
                                    continue

                            # If we get here, either max retries exceeded or non-rate-limit error
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

                    # Log final status
                    BatchLogService.create_log(
                        batch_id,
                        'PROFILE_CHECK_END',
                        f'Check complete for profile {batch_profile.profile.username}',
                        profile_id=batch_profile.profile.id
                    )

                    # Add delay between profiles to help prevent rate limiting
                    await asyncio.sleep(20)  # 20 second delay between profiles

                finally:
                    logger.info(f'8. Releasing worker with proxy {worker.proxy_session.proxy_url_safe}')
                    await worker_pool.release_worker(worker)
                    await asyncio.sleep(1)  # Brief pause before next profile

                # Always mark profile as completed and commit
                batch.completed_profiles += 1
                db.session.commit()

            # Complete batch and start next one
            logger.info("9. Batch processing complete")

            # Mark current batch as completed using QueueManager
            logger.info(f'Marking batch {batch.id} as completed')
            with app.app_context():
                QueueManager.mark_completed(batch.id)

            # Set completed_at timestamp and commit
            batch.completed_at = datetime.now(UTC)
            db.session.commit()

            logger.info(f'Batch {batch.id} completed: {batch.successful_checks} successful, {batch.failed_checks} failed')
            BatchLogService.create_log(
                batch_id,
                'BATCH_END',
                f'Batch completed: {batch.successful_checks} successful, {batch.failed_checks} failed'
            )

            worker_pool.unregister_batch(batch_id)
            logger.info(f'Unregistered batch {batch_id} from worker pool')

    except Exception as e:
        logger.error(f'Error processing batch {batch_id}: {e}', exc_info=True)
        BatchLogService.create_log(batch_id, 'BATCH_ERROR', f'Error processing batch: {str(e)}')
        if batch:
            QueueManager.move_to_end(batch)
            batch.completed_profiles = 0
            batch.successful_checks = 0
            batch.failed_checks = 0
            db.session.commit()

def process_batch(batch_id: str):
    """Process a single batch"""
    # Get app reference before entering context
    from flask import current_app as app

    logger.info(f"=== Starting process_batch for batch_id: {batch_id} ===")

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        with app.app_context():
            # Get worker pool
            logger.info("1. Getting worker pool...")
            worker_pool = getattr(app, 'worker_pool', None)
            logger.info(f"2. Worker pool obtained: {worker_pool is not None}")
            if not worker_pool:
                logger.error('No worker pool available')
                BatchLogService.create_log(batch_id, 'ERROR', 'No worker pool available')
                return

            # Verify batch exists before logging
            logger.info("3. Verifying batch exists...")
            batch = db.session.get(Batch, batch_id)
            if not batch:
                logger.error(f'Batch {batch_id} not found')
                BatchLogService.create_log(batch_id, 'ERROR', f'Batch {batch_id} not found')
                return

            # Run the async process_batch function
            logger.info(f"4. Running process_batch_async for batch_id: {batch_id}")
            try:
                loop.run_until_complete(process_batch_async(batch_id, worker_pool))
            except Exception as e:
                logger.error(f'Error in process_batch_async: {e}', exc_info=True)
                BatchLogService.create_log(batch_id, 'ERROR', f'Error in process_batch_async: {str(e)}')
                if batch:
                    # Import move_to_end after error to avoid circular imports
                    from services.queue_manager import QueueManager
                    QueueManager.move_to_end(batch)
                    batch.completed_profiles = 0
                    batch.successful_checks = 0
                    batch.failed_checks = 0
                    db.session.commit()
                raise

    except Exception as e:
        with app.app_context():
            logger.error(f'Error processing batch {batch_id}: {e}', exc_info=True)
            BatchLogService.create_log(batch_id, 'ERROR', f'Error processing batch: {str(e)}')
            # Reset batch status on error
            try:
                batch = db.session.get(Batch, batch_id)
                if batch and batch.queue_position == 0:  # Only handle running batch
                    # Import move_to_end after error to avoid circular imports
                    from services.queue_manager import QueueManager
                    QueueManager.move_to_end(batch)
                    batch.completed_profiles = 0
                    batch.successful_checks = 0
                    batch.failed_checks = 0
                    db.session.commit()
            except Exception as e:
                logger.error(f'Error resetting batch status: {e}', exc_info=True)
    finally:
        loop.close()
        with app.app_context():
            logger.info(f"=== Finished process_batch for batch_id: {batch_id} ===")
            BatchLogService.create_log(batch_id, 'INFO', f'Finished process_batch for batch_id: {batch_id}')
