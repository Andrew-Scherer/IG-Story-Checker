"""
API Package
Registers API blueprints and initializes API routes
"""

from flask import Blueprint
from .niche import niche_bp
from .profile import profile_bp
from .batch import batch_bp
from .settings import settings_bp

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Register route blueprints
api_bp.register_blueprint(niche_bp)
api_bp.register_blueprint(profile_bp)
api_bp.register_blueprint(batch_bp)
api_bp.register_blueprint(settings_bp)

# Export blueprints
__all__ = ['api_bp']
