# Worker Manager Module

from core.worker.pool import WorkerPool
from models import Proxy, Session
from services.batch_log_service import BatchLogService

def initialize_worker_pool(app, db):
    """Initialize the worker pool and load proxies and sessions."""
    try:
        with app.app_context():
            app.logger.info("=== Initializing Worker Pool ===")
            app.logger.info("1. Creating worker pool...")
            app.worker_pool = WorkerPool(max_workers=5)
            
            app.logger.info("2. Loading proxies and sessions...")
            proxies = Proxy.query.all()
            app.logger.info(f"3. Found {len(proxies)} proxies")
            
            for proxy in proxies:
                try:
                    session = Session.query.filter_by(proxy_id=proxy.id).first()
                    if session:
                        proxy_url = f"http://{proxy.ip}:{proxy.port}"
                        app.worker_pool.add_proxy_session(proxy_url, session.session)
                        app.logger.info(f"4. Added proxy {proxy_url} with session {session.id} to WorkerPool")
                    else:
                        app.logger.warning(f"No session found for proxy {proxy.ip}:{proxy.port}, skipping")
                except Exception as e:
                    app.logger.error(f"Error adding proxy {proxy.ip}:{proxy.port}: {str(e)}")
                    # Continue with other proxies even if one fails
                    continue
                    
            app.logger.info("5. Worker pool initialization complete")
            return True
            
    except Exception as e:
        app.logger.error(f"Failed to initialize worker pool: {str(e)}")
        # Clean up if initialization fails
        if hasattr(app, 'worker_pool'):
            del app.worker_pool
        raise
