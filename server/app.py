# Add the server directory to Python path first
import os
import sys
from pathlib import Path

server_dir = Path(__file__).resolve().parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

# Flask application factory
from dotenv import load_dotenv
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS
from extensions import db
from config.logging_config import setup_component_logging

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
env_path = Path('.') / '.env'
if not env_path.exists():
    print("Error: .env file not found in", os.path.abspath('.'))
    sys.exit(1)

load_dotenv(env_path, verbose=True)

# Verify database environment variables
required_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB']
env_values = {var: os.getenv(var) for var in required_vars}
print("Database environment variables:")
for var, value in env_values.items():
    print(f"{var}: {value}")

missing_vars = [var for var in required_vars if not env_values[var]]
if missing_vars:
    print("Error: Missing required environment variables:", missing_vars)
    sys.exit(1)

# Also check SQLAlchemy URI
print("SQLALCHEMY_DATABASE_URI:", os.getenv('SQLALCHEMY_DATABASE_URI'))

def create_app(config_object=None):
    """Create Flask application"""
    # Set up application logging
    logger = setup_component_logging('app')
    logger.info("=== Starting Flask Application Creation ===")

    app = Flask(__name__)
    app.logger = logger
    logger.info("[OK] Flask app instance created")

    # Add request logging
    @app.before_request
    def log_request_info():
        logger.info('=== New Request ===')
        logger.info(f'Headers: {dict(request.headers)}')
        logger.info(f'Method: {request.method}')
        logger.info(f'URL: {request.url}')
        logger.info(f'Data: {request.get_data()}')

    # Register error handlers
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f'Unhandled error: {str(error)}', exc_info=True)
        if hasattr(error, 'to_dict'):
            response = error.to_dict()
        else:
            response = {'error': str(error)}
            if app.debug:
                import traceback
                response['traceback'] = traceback.format_exc()
        return jsonify(response), getattr(error, 'code', 500)

    # Load config
    logger.info("=== Loading Configuration ===")
    if config_object is None:
        # Import here to avoid circular imports
        import importlib.util
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.py')
        spec = importlib.util.spec_from_file_location('config', config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        config_object = config_module.DevelopmentConfig()
        logger.info("[OK] Using development configuration")
    if isinstance(config_object, dict):
        app.config.update(config_object)
        logger.info("[OK] Updated config from dictionary")
    else:
        app.config.from_object(config_object)
        logger.info("[OK] Loaded config from object")

    # Print final configuration for debugging
    print("\nFinal configuration:")
    print(f"SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"DEBUG: {app.config.get('DEBUG')}")
    print(f"TESTING: {app.config.get('TESTING')}")
    print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}\n")

    # Initialize CORS with settings from config
    logger.info("=== Initializing CORS ===")
    cors_settings = app.config.get('CORS_SETTINGS', {})
    CORS(app, **cors_settings)
    logger.info("[OK] CORS initialized")
    
    # Initialize database with debug logging
    db.init_app(app)
    with app.app_context():
        try:
            # Test database connection
            db.engine.connect()
            logger.info("[OK] Database connection test successful")
            # Log database configuration
            logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
            logger.info(f"Database options: {app.config['SQLALCHEMY_ENGINE_OPTIONS']}")
        except Exception as e:
            logger.error(f"[ERROR] Database connection failed: {str(e)}")
            raise
    logger.info("[OK] Database initialized")

    # Register API blueprints
    logger.info("=== Registering Blueprints ===")
    from api import api_bp
    app.register_blueprint(api_bp)
    logger.info("[OK] API blueprints registered")

    # Create all tables if they don't exist
    with app.app_context():
        # Check if tables exist by trying to query one
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            db.create_all()
            logger.info("[OK] Database tables created")
        else:
            logger.info("[OK] Database tables already exist")

    return app

import threading
import asyncio
from core.batch_processor import process_batches

app = create_app()

def start_batch_processor():
    with app.app_context():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(batch_processor_loop())
        finally:
            loop.close()

async def batch_processor_loop():
    while True:
        await process_batches()
        await asyncio.sleep(5)

if __name__ == '__main__':
    # Start the batch processor in a separate daemon thread
    threading.Thread(target=start_batch_processor, daemon=True).start()

    # Run the application
    try:
        print("\n=== Starting Flask Server ===")
        print(f"Host: 0.0.0.0")
        print(f"Port: 5000")
        print(f"Debug: {app.config.get('DEBUG')}")
        print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        print(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print("=== Server Configuration ===")
        print(f"CORS Origins: {app.config.get('CORS_SETTINGS', {}).get('origins', ['http://localhost:3000'])}")
        print("=== Starting Server ===\n")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True
        )
    except Exception as e:
        print(f"\n!!! Error starting server !!!")
        print(f"Error: {str(e)}")
        print("Stack trace:")
        import traceback
        traceback.print_exc()
