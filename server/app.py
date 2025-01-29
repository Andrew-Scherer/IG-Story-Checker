# Flask application factory

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add the server directory to Python path
server_dir = Path(__file__).resolve().parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

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

    # Initialize extensions with proper CORS configuration
    logger.info("=== Initializing Extensions ===")
    cors = CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"]
        }
    })
    
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin in ["http://localhost:3000", "http://127.0.0.1:3000"]:
            response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    logger.info("[OK] CORS initialized")
    db.init_app(app)
    logger.info("[OK] Database initialized")

    # Register API blueprints
    logger.info("=== Registering Blueprints ===")
    from api import api_bp
    app.register_blueprint(api_bp)
    logger.info("[OK] API blueprints registered")

    # Create all tables if they don't exist
    with app.app_context():
        db.create_all()
        logger.info("[OK] Database tables created or verified")

    return app

if __name__ == '__main__':
    app = create_app()

    # Run the application
    app.run(port=5000, debug=True)  # Enable debug mode to show error tracebacks
