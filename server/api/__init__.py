"""
API Package
Registers API blueprints and initializes API routes

IMPORTANT: This file defines the core API route structure.
DO NOT modify the blueprint registration or URL prefixes
as it will break frontend API calls.

See README.md for detailed API route documentation.

Route Structure:
/api
  /niches    -> niche_bp
  /profiles  -> profile_bp
  /batches   -> batch_bp
  /settings  -> settings_bp
  /proxies   -> proxy_bp
"""

from flask import Blueprint
from .niche import niche_bp
from .profile import profile_bp
from .batch import batch_bp
from .settings import settings_bp
from .proxy import proxy_bp
from .proxy_error_log import proxy_error_log_bp

# Create API blueprint with /api prefix
api_bp = Blueprint('api', __name__, url_prefix='/api')
api_bp.register_blueprint(niche_bp, url_prefix='/niches')
api_bp.register_blueprint(profile_bp, url_prefix='/profiles')
api_bp.register_blueprint(batch_bp, url_prefix='/batches')
api_bp.register_blueprint(settings_bp, url_prefix='/settings')
api_bp.register_blueprint(proxy_bp, url_prefix='/proxies')
api_bp.register_blueprint(proxy_error_log_bp)

# Export blueprints
__all__ = ['api_bp']
