"""
Settings Models
Manages system settings
"""

from .base import BaseModel, db

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
    proxy_hourly_limit = db.Column(db.Integer, default=150)  # requests per hour per proxy-session
    
    # Notification settings
    notifications_enabled = db.Column(db.Boolean, default=True)
    notification_email = db.Column(db.String(255), nullable=True)

    @classmethod
    def get_settings(cls):
        """Get or create system settings"""
        settings = db.session.get(cls, 1)
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
            **super().to_dict(),
            'profiles_per_minute': self.profiles_per_minute,
            'max_threads': self.max_threads,
            'default_batch_size': self.default_batch_size,
            'story_retention_hours': self.story_retention_hours,
            'auto_trigger_enabled': self.auto_trigger_enabled,
            'min_trigger_interval': self.min_trigger_interval,
            'proxy_test_timeout': self.proxy_test_timeout,
            'proxy_max_failures': self.proxy_max_failures,
            'proxy_hourly_limit': self.proxy_hourly_limit,
            'notifications_enabled': self.notifications_enabled,
            'notification_email': self.notification_email
        }
