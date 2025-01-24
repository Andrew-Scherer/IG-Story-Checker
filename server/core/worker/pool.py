"""
Worker Pool Management
Manages pool of workers for story checking
"""

from typing import List, Optional, Set
from datetime import datetime, UTC
from threading import Lock
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from models.settings import SystemSettings
from models.proxy import Proxy
from models.session import Session
from models import db, Batch
from core.proxy_session import ProxySession
from .worker import Worker
from core.proxy_manager import ProxyManager
from flask import current_app

class WorkerPool:
    """Manages pool of story checking workers"""
    
    def __init__(self, max_workers: int):
        """Initialize worker pool"""
        current_app.logger.info(f'=== Initializing Worker Pool ===')
        current_app.logger.info(f'1. Setting max workers to {max_workers}')
        self.max_workers = max_workers
        self.active_workers: List[Worker] = []
        self.running_batches: Set[str] = set()
        self.proxy_manager = ProxyManager()
        self._lock = Lock()
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: dict[str, Future] = {}  # Track futures by batch_id
        current_app.logger.info('2. Worker pool initialized successfully')
        
    def add_proxy_session(self, proxy_url: str, session_cookie: str) -> None:
        """Add new proxy-session pair
        
        Args:
            proxy_url: Full proxy URL
            session_cookie: Session cookie
        """
        current_app.logger.info(f'Adding proxy session for {proxy_url}')
        self.proxy_manager.add_proxy(proxy_url, session_cookie)
        current_app.logger.info(f'Successfully added proxy session')
        
    def remove_proxy_session(self, proxy_url: str) -> None:
        """Remove proxy-session pair"""
        current_app.logger.info(f'Removing proxy session for {proxy_url}')
        self.proxy_manager.remove_proxy(proxy_url)
        # Remove any active workers using this proxy
        self.active_workers = [w for w in self.active_workers if w.proxy_session.proxy_url != proxy_url]
        current_app.logger.info(f'Successfully removed proxy session')
        
    PROXY_COOLDOWN = 20  # Seconds between proxy uses
    
    def get_worker(self) -> Optional[Worker]:
        """Get available worker using round-robin rotation with atomic locking
        
        Returns:
            Worker if available and validated, None otherwise
        """
        current_app.logger.info('=== Getting Worker ===')
        with self._lock:
            if len(self.active_workers) >= self.max_workers:
                current_app.logger.debug('Worker pool at capacity')
                return None

            # Sync proxy states before selection
            current_app.logger.info('1. Syncing proxy states...')
            self.proxy_manager.sync_states()
            
            # Get proxy with cooldown and health check
            current_app.logger.info('2. Getting available proxy...')
            proxy_url = self.proxy_manager.get_available_proxy(self.PROXY_COOLDOWN)
            if not proxy_url:
                current_app.logger.debug('No proxies available after cooldown and health checks')
                return None

            # Verify proxy health state
            current_app.logger.info('3. Verifying proxy health...')
            proxy_state = self.proxy_manager.get_proxy_state(proxy_url)
            if proxy_state['disabled'] or proxy_state['rate_limited']:
                current_app.logger.warning(f'Skipping proxy {proxy_url} - disabled: {proxy_state["disabled"]}, rate limited: {proxy_state["rate_limited"]}')
                return None

            # Validate session
            current_app.logger.info('4. Validating session...')
            session_data = self.proxy_manager.get_session(proxy_url)
            if not session_data:
                current_app.logger.error(f'No session data for proxy {proxy_url}')
                return None
                
            session_cookie, proxy_id = session_data
            
            # Verify database records
            current_app.logger.info('5. Verifying database records...')
            proxy = Proxy.query.get(proxy_id)
            if not proxy or not proxy.is_active:
                current_app.logger.error(f'Proxy {proxy_id} not found or disabled')
                self.proxy_manager.update_state(proxy_url, disabled=True)
                return None
                
            session = Session.query.filter_by(proxy_id=proxy_id).first()
            if not session or not session.is_valid():
                current_app.logger.error(f'Invalid session for proxy {proxy_id}')
                return None

            try:
                # Create and validate worker
                current_app.logger.info('6. Creating worker...')
                worker = Worker(proxy, session)
                
                # Initial health check
                current_app.logger.info('7. Performing initial health check...')
                if worker.is_disabled or worker.is_rate_limited:
                    current_app.logger.warning(f'New worker created in bad state - disabled: {worker.is_disabled}, rate limited: {worker.is_rate_limited}')
                    self.proxy_manager.update_state(proxy_url, disabled=worker.is_disabled, rate_limited=worker.is_rate_limited)
                    return None
                    
                # Verify session initialization
                if not worker.proxy_session.session.is_valid():
                    current_app.logger.error('Worker created with expired session')
                    return None

                self.active_workers.append(worker)
                current_app.logger.info(f'8. Successfully created healthy worker with proxy {worker.proxy_session.proxy_url_safe}')
                return worker
                
            except Exception as e:
                current_app.logger.error(f'Worker creation failed: {str(e)}')
                return None
        
    async def release_worker(self, worker: Worker) -> None:
        """Return worker to available pool
        
        Args:
            worker: Worker to release
        """
        current_app.logger.info(f'=== Releasing Worker ===')
        try:
            # Clean up worker's story checker session
            current_app.logger.info('1. Cleaning up story checker session...')
            await worker.story_checker.cleanup()
                
            if worker in self.active_workers:
                current_app.logger.info('2. Removing from active workers...')
                self.active_workers.remove(worker)
                
            # Update proxy state
            current_app.logger.info('3. Updating proxy state...')
            self.proxy_manager.update_state(
                worker.proxy_session.proxy_url,
                disabled=worker.is_disabled,
                rate_limited=worker.is_rate_limited
            )
            
            # Update last used time if not disabled/rate-limited
            if not worker.is_disabled and not worker.is_rate_limited:
                current_app.logger.info('4. Updating last used time...')
                self.proxy_manager.update_last_used(worker.proxy_session.proxy_url)
                
            current_app.logger.info('5. Worker released successfully')
                
        except Exception as e:
            current_app.logger.error(f'Error releasing worker: {e}')
    
    def register_batch(self, batch_id: str) -> None:
        """Register a batch as running
        
        Args:
            batch_id: ID of the batch to register
        """
        current_app.logger.info(f'=== Registering Batch {batch_id} ===')
        with self._lock:
            self.running_batches.add(batch_id)
            current_app.logger.info(f'Batch {batch_id} registered as running')
    
    def unregister_batch(self, batch_id: str) -> None:
        """Unregister a batch as no longer running
        
        Args:
            batch_id: ID of the batch to unregister
        """
        current_app.logger.info(f'=== Unregistering Batch {batch_id} ===')
        with self._lock:
            if batch_id in self.running_batches:
                current_app.logger.info('1. Removing from running batches...')
                self.running_batches.remove(batch_id)
                # Cancel any running future
                if batch_id in self._futures:
                    current_app.logger.info('2. Cancelling future...')
                    future = self._futures[batch_id]
                    if not future.done():
                        future.cancel()
                    del self._futures[batch_id]
                current_app.logger.info(f'3. Successfully unregistered batch {batch_id}')
    
    def get_running_batch_ids(self) -> List[str]:
        """Return a list of currently running batch IDs"""
        return list(self.running_batches)

    def submit(self, fn, batch_id: str, *args, **kwargs) -> Future:
        """Submit a task to be executed.

        Args:
            fn: The function to execute.
            batch_id: ID of the batch being processed.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Future: A Future representing the execution of the task.
        """
        app = current_app._get_current_object()
        app.logger.info(f"=== Submitting Batch {batch_id} ===")
        
        def wrapped_fn():
            try:
                # Create app context for this thread
                with app.app_context():
                    app.logger.info(f"1. Starting execution of batch {batch_id}")
                    return fn(batch_id, *args, **kwargs)
            except Exception as e:
                app.logger.error(f"Error executing batch {batch_id}: {e}")
                raise

        def done_callback(future):
            # Use app object from outer scope

            # Always clean up future first
            with self._lock:
                if batch_id in self._futures and self._futures[batch_id] is future:
                    del self._futures[batch_id]

            try:
                with app.app_context():
                    # Check for exceptions
                    if future.exception():
                        app.logger.error(f'Batch {batch_id} failed: {future.exception()}')
                        batch = db.session.get(Batch, batch_id)
                        if batch:
                            batch.status = 'queued'  # Reset to queued on failure
                            db.session.commit()
                    else:
                        app.logger.info(f'Batch {batch_id} completed successfully')
            except Exception as e:
                # Create new context for error logging
                with app.app_context():
                    app.logger.error(f'Error in future callback: {e}')
        
        # Submit task to thread pool and store future
        current_app.logger.info(f"2. Submitting batch to thread pool...")
        future = self._thread_pool.submit(wrapped_fn)
        app.logger.info(f"Future created: {future}")
        future.add_done_callback(done_callback)
        self._futures[batch_id] = future
        current_app.logger.info(f"3. Batch {batch_id} submitted successfully")
        app.logger.info(f"4. Returning future: {future}")
        return future
