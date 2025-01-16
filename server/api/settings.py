"""
Settings API Resources
Handles system settings and proxy management endpoints
"""

from flask import request
from flask_restful import Resource, reqparse, fields, marshal_with, abort
from datetime import datetime
from models import db, SystemSettings, Proxy

# Response fields
settings_fields = {
    'profiles_per_minute': fields.Integer,
    'max_threads': fields.Integer,
    'default_batch_size': fields.Integer,
    'story_retention_hours': fields.Integer,
    'auto_trigger_enabled': fields.Boolean,
    'min_trigger_interval': fields.Integer,
    'proxy_test_timeout': fields.Integer,
    'proxy_max_failures': fields.Integer,
    'notifications_enabled': fields.Boolean,
    'notification_email': fields.String,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601')
}

proxy_fields = {
    'id': fields.String,
    'host': fields.String,
    'port': fields.Integer,
    'username': fields.String,
    'is_active': fields.Boolean,
    'is_working': fields.Boolean,
    'last_used': fields.DateTime(dt_format='iso8601'),
    'last_tested': fields.DateTime(dt_format='iso8601'),
    'error': fields.String,
    'total_requests': fields.Integer,
    'failed_requests': fields.Integer,
    'average_response_time': fields.Float,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601')
}

# Request parsers
settings_parser = reqparse.RequestParser()
settings_parser.add_argument('profiles_per_minute', type=int)
settings_parser.add_argument('max_threads', type=int)
settings_parser.add_argument('default_batch_size', type=int)
settings_parser.add_argument('story_retention_hours', type=int)
settings_parser.add_argument('auto_trigger_enabled', type=bool)
settings_parser.add_argument('min_trigger_interval', type=int)
settings_parser.add_argument('proxy_test_timeout', type=int)
settings_parser.add_argument('proxy_max_failures', type=int)
settings_parser.add_argument('notifications_enabled', type=bool)
settings_parser.add_argument('notification_email', type=str)

proxy_parser = reqparse.RequestParser()
proxy_parser.add_argument('host', type=str, required=True, help='Host is required')
proxy_parser.add_argument('port', type=int, required=True, help='Port is required')
proxy_parser.add_argument('username', type=str)
proxy_parser.add_argument('password', type=str)
proxy_parser.add_argument('is_active', type=bool)

class SystemSettingsResource(Resource):
    """Resource for managing system settings"""
    
    @marshal_with(settings_fields)
    def get(self):
        """Get current system settings"""
        return SystemSettings.get_settings()

    @marshal_with(settings_fields)
    def put(self):
        """Update system settings"""
        settings = SystemSettings.get_settings()
        args = settings_parser.parse_args()
        
        # Validate numeric settings
        if args.get('profiles_per_minute', 0) <= 0:
            abort(400, message='Profiles per minute must be positive')
        if args.get('max_threads', 0) <= 0:
            abort(400, message='Max threads must be positive')
        if args.get('story_retention_hours', 0) <= 0:
            abort(400, message='Story retention hours must be positive')
        
        # Update settings
        for key, value in args.items():
            if value is not None:
                setattr(settings, key, value)
        
        settings.save()
        return settings

class ProxyListResource(Resource):
    """Resource for managing proxy collections"""
    
    @marshal_with(proxy_fields)
    def get(self):
        """Get all proxies"""
        return Proxy.query.all()

    @marshal_with(proxy_fields)
    def post(self):
        """Add new proxy"""
        args = proxy_parser.parse_args()
        
        # Validate port
        if args['port'] <= 0 or args['port'] > 65535:
            abort(400, message='Invalid port number')
        
        # Create proxy
        proxy = Proxy(
            host=args['host'],
            port=args['port'],
            username=args.get('username'),
            password=args.get('password')
        )
        proxy.save()
        
        return proxy, 201

class ProxyResource(Resource):
    """Resource for managing individual proxies"""
    
    @marshal_with(proxy_fields)
    def get(self, proxy_id):
        """Get specific proxy"""
        proxy = Proxy.get_by_id(proxy_id)
        if not proxy:
            abort(404, message=f"Proxy {proxy_id} not found")
        return proxy

    @marshal_with(proxy_fields)
    def put(self, proxy_id):
        """Update proxy"""
        proxy = Proxy.get_by_id(proxy_id)
        if not proxy:
            abort(404, message=f"Proxy {proxy_id} not found")
        
        args = proxy_parser.parse_args()
        
        # Validate port if changing
        if args['port'] <= 0 or args['port'] > 65535:
            abort(400, message='Invalid port number')
        
        # Update fields
        proxy.host = args['host']
        proxy.port = args['port']
        proxy.username = args.get('username')
        if args.get('password'):
            proxy.password = args['password']
        if args.get('is_active') is not None:
            proxy.is_active = args['is_active']
        
        proxy.save()
        return proxy

    def delete(self, proxy_id):
        """Delete proxy"""
        proxy = Proxy.get_by_id(proxy_id)
        if not proxy:
            abort(404, message=f"Proxy {proxy_id} not found")
        
        proxy.delete()
        return '', 204

class ProxyTestResource(Resource):
    """Resource for proxy testing"""
    
    def post(self, proxy_id=None):
        """Test proxy connection"""
        if proxy_id:
            # Test single proxy
            proxy = Proxy.get_by_id(proxy_id)
            if not proxy:
                abort(404, message=f"Proxy {proxy_id} not found")
            
            result = proxy.test_connection()
            return {
                'id': proxy.id,
                'is_working': result['success'],
                'error': result.get('error')
            }
        else:
            # Test all active proxies
            results = []
            for proxy in Proxy.query.filter_by(is_active=True):
                result = proxy.test_connection()
                results.append({
                    'id': proxy.id,
                    'is_working': result['success'],
                    'error': result.get('error')
                })
            return {'results': results}

class ProxyStatsResource(Resource):
    """Resource for proxy statistics"""
    
    def get(self, proxy_id):
        """Get proxy usage statistics"""
        proxy = Proxy.get_by_id(proxy_id)
        if not proxy:
            abort(404, message=f"Proxy {proxy_id} not found")
        
        return {
            'total_requests': proxy.total_requests,
            'failed_requests': proxy.failed_requests,
            'average_response_time': proxy.average_response_time,
            'last_used': proxy.last_used.isoformat() if proxy.last_used else None,
            'last_tested': proxy.last_tested.isoformat() if proxy.last_tested else None
        }

class ProxyRotateResource(Resource):
    """Resource for proxy rotation"""
    
    def post(self):
        """Rotate active proxies"""
        # Get active proxies
        active_proxies = Proxy.query.filter_by(is_active=True).all()
        
        # Test and update status
        for proxy in active_proxies:
            result = proxy.test_connection()
            proxy.is_working = result['success']
            proxy.error = result.get('error')
            proxy.last_tested = datetime.utcnow()
            proxy.save()
        
        return {'rotated': len(active_proxies)}
