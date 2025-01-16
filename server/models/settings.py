"""
Settings Models
Manages proxy configurations and system settings
"""

import uuid
from datetime import datetime
from .base import BaseModel, db

class Proxy(BaseModel):
    """Proxy configuration model"""
    __tablename__ = 'proxies'

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Proxy configuration
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime, nullable=True)
    last_tested = db.Column(db.DateTime, nullable=True)
    is_working = db.Column(db.Boolean, default=False)
    error = db.Column(db.String(255), nullable=True)
    
    # Statistics
    total_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    average_response_time = db.Column(db.Float, nullable=True)

    def __init__(self, host, port, username=None, password=None):
        """Initialize a new proxy"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @property
    def url(self):
        """Get proxy URL"""
        auth = f'{self.username}:{self.password}@' if self.username else ''
        return f'http://{auth}{self.host}:{self.port}'

    def update_stats(self, success, response_time=None):
        """Update proxy statistics"""
        self.last_used = datetime.utcnow()
        self.total_requests += 1
        
        if not success:
            self.failed_requests += 1
        
        if response_time:
            if self.average_response_time:
                self.average_response_time = (
                    self.average_response_time * 0.9 + response_time * 0.1
                )
            else:
                self.average_response_time = response_time
        
        self.save()

    def test_connection(self):
        """Test proxy connection"""
        # TODO: Implementation
        # 1. Try connecting to test URL
        # 2. Update status
        # 3. Record results
        pass

    @classmethod
    def get_next_available(cls):
        """Get next available proxy using round-robin"""
        return cls.query.filter_by(
            is_active=True,
            is_working=True
        ).order_by(
            cls.last_used.asc().nullsfirst()
        ).first()

    def to_dict(self):
        """Convert proxy to dictionary"""
        return {
            **super().to_dict(),
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'is_active': self.is_active,
            'is_working': self.is_working,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'error': self.error,
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'average_response_time': self.average_response_time
        }

class SystemSettings(BaseModel):
    """System-wide settings model"""
    __tablename__ = 'system_settings'

    # Primary key (only one record)
    id = db.Column(db.Integer, primary_key=True, default=1)
    
    # Rate limiting
    profiles_per_minute = db.Column(db.Integer, default=30)
    max_threads = db.Column(db.Integer, default=3)
    default_batch_size = db.Column(db.Integer, default=100)
    
    # Story settings
    story_retention_hours = db.Column(db.Integer, default=24)
    
    # Batch settings
    auto_trigger_enabled = db.Column(db.Boolean, default=True)
    min_trigger_interval = db.Column(db.Integer, default=60)  # minutes
    
    # Proxy settings
    proxy_test_timeout = db.Column(db.Integer, default=10)  # seconds
    proxy_max_failures = db.Column(db.Integer, default=3)
    
    # Notification settings
    notifications_enabled = db.Column(db.Boolean, default=True)
    notification_email = db.Column(db.String(255), nullable=True)

    @classmethod
    def get_settings(cls):
        """Get or create system settings"""
        settings = cls.query.get(1)
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def update(self, **kwargs):
        """Update settings"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

    def to_dict(self):
        """Convert settings to dictionary"""
        return {
            'profiles_per_minute': self.profiles_per_minute,
            'max_threads': self.max_threads,
            'default_batch_size': self.default_batch_size,
            'story_retention_hours': self.story_retention_hours,
            'auto_trigger_enabled': self.auto_trigger_enabled,
            'min_trigger_interval': self.min_trigger_interval,
            'proxy_test_timeout': self.proxy_test_timeout,
            'proxy_max_failures': self.proxy_max_failures,
            'notifications_enabled': self.notifications_enabled,
            'notification_email': self.notification_email
        }
