"""
Worker Pool Management
Manages pool of workers for story checking
"""

from typing import List, Optional, Set
from datetime import datetime, UTC
from threading import Lock
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
        self.proxy_manager = ProxyManager(db.session)
        self._lock = Lock()
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: dict[str, Future] = {}  # Track futures by batch_id
        current_app.logger.info('2. Worker pool initialized successfully')
        
    def add_proxies(self, proxies: List[Proxy]) -> None:
        """Add proxies to the proxy manager

        Args:
            proxies: List of Proxy objects
        """
        current_app.logger.info('=== Adding proxies to the pool ===')
        for proxy in proxies:
            try:
                current_app.logger.info(f'Processing proxy {proxy.ip}:{proxy.port}')
                
                # Verify proxy is active
                if not proxy.is_active:
                    current_app.logger.warning(f'Skipping inactive proxy {proxy.ip}:{proxy.port}')
                    continue
                
                # Get associated session
                session = Session.query.filter_by(proxy_id=proxy.id).first()
                if not session:
                    current_app.logger.warning(f'No session found for proxy {proxy.ip}:{proxy.port}, skipping')
                    continue
                
                if not session.is_valid():
                    current_app.logger.warning(f'Invalid session for proxy {proxy.ip}:{proxy.port}, skipping')
                    continue
                
                # Build http:// URL with auth if available
                proxy_url = f"http://{proxy.ip}:{proxy.port}"
                if proxy.username and proxy.password:
                    proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
                
                current_app.logger.debug(f'Adding proxy with URL: {proxy_url}')
                result = self.proxy_manager.session_manager.add_proxy(proxy_url, session.session)
                
                if result is not None:
                    current_app.logger.info(f'Successfully added proxy {proxy.ip}:{proxy.port} with session {session.id}')
                else:
                    current_app.logger.error(f'Failed to add proxy {proxy.ip}:{proxy.port} to session manager')
                
            except Exception as e:
                current_app.logger.error(f'Error adding proxy {proxy.ip}:{proxy.port}: {str(e)}')

    PROXY_COOLDOWN = 20  # Seconds between proxy uses

    def get_worker(self) -> Optional[Worker]:
        """Get available worker using the updated ProxyManager

        Returns:
            Worker if available and validated, None otherwise
        """
        current_app.logger.info('=== Getting Worker ===')
        with self._lock:
            if len(self.active_workers) >= self.max_workers:
                current_app.logger.debug('Worker pool at capacity')
                return None

            # Get next available proxy
            current_app.logger.info('1. Getting next available proxy...')
            proxy = self.proxy_manager.get_next_proxy()
            if not proxy:
                current_app.logger.debug('No proxies available')
                return None

            # Check if proxy is healthy
            current_app.logger.info('2. Checking if proxy is healthy...')
            if not self.proxy_manager.is_proxy_healthy(proxy):
                current_app.logger.warning(f'Proxy {proxy.ip}:{proxy.port} is not healthy')
                return None

            # Get session cookie from session manager
            current_app.logger.info('3. Getting session cookie...')
            # Build http:// URL with auth if available
            proxy_url = f"http://{proxy.ip}:{proxy.port}"
            if proxy.username and proxy.password:
                proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
            session_data = self.proxy_manager.session_manager.get_session(proxy_url)
            if not session_data:
                current_app.logger.error(f'No session data for proxy {proxy.ip}:{proxy.port}')
                return None
            session_cookie, proxy_id = session_data

            # Verify database records
            current_app.logger.info('4. Verifying database records...')
            session = Session.query.filter_by(proxy_id=proxy.id).first()
            if not session or not session.is_valid():
                current_app.logger.error(f'Invalid session for proxy {proxy.ip}:{proxy.port}')
                return None

            # Create and validate worker
            current_app.logger.info('5. Creating worker...')
            try:
                worker = Worker(proxy, session)
            except Exception as e:
                current_app.logger.error(f'Failed to create worker for proxy {proxy.ip}:{proxy.port}: {str(e)}')
                # Record error in proxy
                proxy.error_count = (proxy.error_count or 0) + 1
                self.db.commit()
                return None

            # Initial health check
            current_app.logger.info('6. Performing initial health check...')
            if worker.is_disabled or worker.is_rate_limited:
                current_app.logger.warning(f'Worker created in bad state - disabled: {worker.is_disabled}, rate limited: {worker.is_rate_limited}')
                self.proxy_manager.health_monitor.cleanup_proxies()
                return None

            # Verify session initialization
            if not worker.proxy_session.session.is_valid():
                current_app.logger.error('Worker created with expired session')
                return None

            self.active_workers.append(worker)
            current_app.logger.info(f'7. Successfully created healthy worker with proxy {proxy.ip}:{proxy.port}')
            return worker

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

            # Record the proxy request
            current_app.logger.info('3. Recording proxy request...')
            self.proxy_manager.record_request(
                proxy=worker.proxy_session.proxy,
                success=not worker.is_disabled and not worker.is_rate_limited,
                response_time=worker.response_time,
                error=worker.error_message
            )

            # Update last used time
            current_app.logger.info('4. Updating last used time...')
            proxy = worker.proxy_session.proxy
            proxy_url = f"http://{proxy.ip}:{proxy.port}"
            if proxy.username and proxy.password:
                proxy_url = f"http://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
            self.proxy_manager.session_manager.update_last_used(proxy_url)

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
