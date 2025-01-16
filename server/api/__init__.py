"""
API Package
Provides REST API endpoints for the application
"""

from flask import Blueprint
from flask_restful import Api

# Create API blueprints
niche_bp = Blueprint('niche', __name__, url_prefix='/api/niches')
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profiles')
batch_bp = Blueprint('batch', __name__, url_prefix='/api/batches')
settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Create API instances
niche_api = Api(niche_bp)
profile_api = Api(profile_bp)
batch_api = Api(batch_bp)
settings_api = Api(settings_bp)

# Import and register resources
from .niche import NicheResource, NicheListResource
from .profile import ProfileResource, ProfileListResource, ProfileImportResource
from .batch import BatchResource, BatchListResource, BatchResultsResource
from .settings import (
    SystemSettingsResource, ProxyResource, ProxyListResource,
    ProxyTestResource
)

# Niche endpoints
niche_api.add_resource(NicheListResource, '')
niche_api.add_resource(NicheResource, '/<string:niche_id>')

# Profile endpoints
profile_api.add_resource(ProfileListResource, '')
profile_api.add_resource(ProfileResource, '/<string:profile_id>')
profile_api.add_resource(ProfileImportResource, '/import')

# Batch endpoints
batch_api.add_resource(BatchListResource, '')
batch_api.add_resource(BatchResource, '/<string:batch_id>')
batch_api.add_resource(BatchResultsResource, '/<string:batch_id>/results')

# Settings endpoints
settings_api.add_resource(SystemSettingsResource, '/system')
settings_api.add_resource(ProxyListResource, '/proxies')
settings_api.add_resource(ProxyResource, '/proxies/<string:proxy_id>')
settings_api.add_resource(ProxyTestResource, '/proxies/<string:proxy_id>/test')

def init_app(app):
    """Register API blueprints with app"""
    app.register_blueprint(niche_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(settings_bp)
