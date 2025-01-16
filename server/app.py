"""
Main Flask Application
Configures and initializes the Flask app with all required extensions
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    from config import get_config
    app.config.from_object(get_config())
    
    # Override with custom config if provided
    if config:
        app.config.update(config)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # TODO: Register blueprints
    # 1. API routes
    # 2. Auth routes
    # 3. Admin routes
    
    # TODO: Initialize background tasks
    # 1. Batch processor
    # 2. Auto-trigger scheduler
    # 3. Result cleanup
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not Found'}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        return {'error': 'Internal Server Error'}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
