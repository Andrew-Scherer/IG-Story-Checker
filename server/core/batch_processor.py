"""
Batch Processor
Handles batch processing and story checking using Celery
"""

from datetime import datetime, UTC
from typing import Optional
from flask import current_app
from extensions import db
from models import Batch, Proxy, Session
from services.batch_manager import BatchManager
from services.batch_log_service import BatchLogService
from core.worker.worker import Worker
from core.proxy_session_manager import ProxySessionManager
from celery import shared_task

@shared_task(bind=True)
def process_batch(self, batch_id):
    """Celery task to process a single batch"""
    app = self.app
    with app.app_context():
        batch = db.session.get(Batch, batch_id)
        if not batch:
            current_app.logger.error(f"Batch {batch_id} not found")
            return

        batch_manager = BatchManager(db.session)
        proxy_manager = ProxySessionManager(db.session)

        try:
            current_app.logger.info(f'=== Processing Batch {batch_id} ===')
            batch_manager.update_status(batch_id, 'processing')

            # Fetch active proxies
            proxies = Proxy.query.filter_by(is_active=True).all()
            if not proxies:
                warning_msg = 'No active proxies available'
                current_app.logger.warning(warning_msg)
                BatchLogService.create_log(batch_id, 'BATCH_PAUSED', warning_msg)
                db.session.commit()
                batch_manager.pause_batch(batch_id)
                return

            # Process each profile in the batch
            batch_profiles = batch.profiles.all()
            for batch_profile in batch_profiles:
                if batch_profile.status == 'completed':
                    continue

                # Assign a proxy and session
                proxy = proxy_manager.get_next_proxy()
                if not proxy:
                    warning_msg = 'No proxies available for profile processing'
                    current_app.logger.warning(warning_msg)
                    BatchLogService.create_log(batch_id, 'BATCH_PAUSED', warning_msg)
                    batch_manager.pause_batch(batch_id)
                    return
                else:
                    BatchLogService.create_log(
                        batch_id,
                        'PROXY_ASSIGNED',
                        f'Assigned proxy {proxy.ip}:{proxy.port} to profile {batch_profile.profile.username}',
                        profile_id=batch_profile.profile.id,
                        proxy_id=proxy.id
                    )

                session = Session.query.filter_by(proxy_id=proxy.id).first()
                if not session or not session.is_valid():
                    current_app.logger.warning(f'Invalid session for proxy {proxy.ip}:{proxy.port}')
                    error_msg = f'Invalid session for proxy {proxy.ip}:{proxy.port} assigned to profile {batch_profile.profile.username}'
                    BatchLogService.create_log(
                        batch_id,
                        'INVALID_SESSION',
                        error_msg,
                        profile_id=batch_profile.profile.id,
                        proxy_id=proxy.id
                    )
                    continue

                worker = Worker(proxy, session)

                # Check story
                current_app.logger.info(f'Checking story for {batch_profile.profile.username}...')
                success, has_story = worker.check_story(batch_profile)

                if success:
                    current_app.logger.info('Story check successful')
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
                    current_app.logger.warning('Story check failed')
                    batch_profile.status = 'failed'
                    batch_profile.processed_at = datetime.now(UTC)
                    batch.failed_checks += 1
                    error_details = str(batch_profile.error or "Unknown error").replace('\x00', '')
                    proxy_details = f"{proxy.ip}:{proxy.port}"
                    error_msg = (
                        f'Failed to check {batch_profile.profile.username} - '
                        f'Error: {error_details} - '
                        f'Proxy: {proxy_details}'
                    )[:500]
                    BatchLogService.create_log(
                        batch_id,
                        'PROFILE_ERROR',
                        error_msg,
                        profile_id=batch_profile.profile.id,
                        proxy_id=proxy.id
                    )

                # Update progress
                current_app.logger.info('Updating batch progress...')
                completed = sum(1 for p in batch_profiles if p.status in ('completed', 'failed'))
                successful = sum(1 for p in batch_profiles if p.has_story)
                failed = sum(1 for p in batch_profiles if p.status == 'failed')
                batch_manager.update_progress(
                    batch_id,
                    completed=completed,
                    successful=successful,
                    failed=failed
                )

                db.session.commit()

            # Check if batch is complete
            if all(p.status in ('completed', 'failed') for p in batch_profiles):
                current_app.logger.info('Batch complete, marking as done')
                batch_manager.complete_batch(batch_id)
            else:
                current_app.logger.info('Batch processing incomplete')

        except Exception as e:
            current_app.logger.error(f'Error processing batch: {str(e)}')
            db.session.rollback()
            batch_manager.handle_error(batch_id, str(e))
            raise self.retry(exc=e, countdown=60)

def enqueue_batches():
    """Function to enqueue pending batches"""
    with current_app.app_context():
        batch_manager = BatchManager(db.session)
        pending_batches = batch_manager.get_pending_batches()

        for batch in pending_batches:
            current_app.logger.info(f'Enqueuing batch {batch.id}')
            process_batch.apply_async(args=[batch.id])

# Optional: Schedule enqueue_batches to run periodically
from celery.schedules import crontab
from app import celery

celery.conf.beat_schedule = {
    'enqueue-batches-every-5-minutes': {
        'task': 'core.batch_processor.enqueue_batches',
        'schedule': crontab(minute='*/5'),
    },
}

# Register the task with Celery
# Removed @celery.on_after_configure.connect decorator to avoid scheduling conflicts
# def setup_periodic_tasks(sender, **kwargs):
#     # Calls enqueue_batches every 5 minutes
#     sender.add_periodic_task(300.0, enqueue_batches.s(), name='Enqueue batches every 5 minutes')
