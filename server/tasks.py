"""
Background tasks and scheduler configuration
"""

import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from api.batch import cleanup_expired_stories
from core.batch_processor import process_batches
from app import create_app

def init_scheduler():
    """Initialize and start the background scheduler"""
    app = create_app()
    scheduler = BackgroundScheduler()
    
    # Add cleanup job to run every 15 minutes
    def cleanup_job():
        with app.app_context():
            cleanup_expired_stories()
    
    # Add batch processor job to run every 30 seconds
    def processor_job():
        with app.app_context():
            asyncio.run(process_batches())
    
    scheduler.add_job(
        func=cleanup_job,
        trigger=IntervalTrigger(minutes=15),
        id='cleanup_expired_stories',
        name='Cleanup expired story detections',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=processor_job,
        trigger=IntervalTrigger(seconds=30),
        id='process_batches',
        name='Process pending batches',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler

def shutdown_scheduler(scheduler):
    """Shutdown the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
