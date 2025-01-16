"""
Application Configuration
Manages different configuration environments and settings
"""

import os
from datetime import timedelta

class BaseConfig:
    """Base configuration"""
    # Application
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Rate Limits
    DEFAULT_RATE_LIMIT = {
        'profiles_per_minute': 30,
        'threads_count': 3,
        'batch_size': 100
    }
    
    # Story Settings
    STORY_RESULT_RETENTION_HOURS = 24
    
    # Redis Cache
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Background Tasks
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'UTC'

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost/ig_story_checker_dev'
    )
    
    # Development-specific settings
    CORS_ORIGINS = ['http://localhost:3000']
    PROXY_TEST_TIMEOUT = 5

class TestingConfig(BaseConfig):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://localhost/ig_story_checker_test'
    )
    
    # Testing-specific settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    STORY_RESULT_RETENTION_HOURS = 1

class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Production-specific settings
    CORS_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')
    PROXY_TEST_TIMEOUT = 10
    
    # Override these in environment variables
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration class based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
