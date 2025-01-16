"""
Settings API Routes
Handles system settings endpoints
"""

import re
from flask import Blueprint, request, jsonify
from models import db, SystemSettings

# Create blueprint
settings_bp = Blueprint('settings', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_settings(data):
    """Validate settings data"""
    errors = []
    
    # Validate numeric fields
    if 'profiles_per_minute' in data and (not isinstance(data['profiles_per_minute'], int) or data['profiles_per_minute'] < 1):
        errors.append("profiles_per_minute must be a positive integer")
    
    if 'max_threads' in data and (not isinstance(data['max_threads'], int) or data['max_threads'] < 1):
        errors.append("max_threads must be a positive integer")
    
    if 'default_batch_size' in data:
        if not isinstance(data['default_batch_size'], int) or data['default_batch_size'] < 1:
            errors.append("default_batch_size must be a positive integer")
        elif data['default_batch_size'] > 10000:  # Reasonable upper limit
            errors.append("default_batch_size is too large")
    
    if 'story_retention_hours' in data and (not isinstance(data['story_retention_hours'], int) or data['story_retention_hours'] < 1):
        errors.append("story_retention_hours must be a positive integer")
    
    if 'min_trigger_interval' in data and (not isinstance(data['min_trigger_interval'], int) or data['min_trigger_interval'] < 1):
        errors.append("min_trigger_interval must be a positive integer")
    
    if 'proxy_test_timeout' in data and (not isinstance(data['proxy_test_timeout'], int) or data['proxy_test_timeout'] < 1):
        errors.append("proxy_test_timeout must be a positive integer")
    
    if 'proxy_max_failures' in data and (not isinstance(data['proxy_max_failures'], int) or data['proxy_max_failures'] < 1):
        errors.append("proxy_max_failures must be a positive integer")
    
    if 'proxy_hourly_limit' in data and (not isinstance(data['proxy_hourly_limit'], int) or data['proxy_hourly_limit'] < 1):
        errors.append("proxy_hourly_limit must be a positive integer")
    
    # Validate email if provided
    if 'notification_email' in data and data['notification_email']:
        if not validate_email(data['notification_email']):
            errors.append("Invalid email format")
    
    return errors

@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get system settings"""
    settings = SystemSettings.get_settings()
    return jsonify(settings.to_dict())

@settings_bp.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update system settings"""
    data = request.get_json()
    
    # Validate settings
    errors = validate_settings(data)
    if errors:
        return jsonify({
            'message': 'Validation errors',
            'errors': errors
        }), 400
    
    # Update settings
    settings = SystemSettings.get_settings()
    settings.update(**data)
    
    return jsonify(settings.to_dict())
