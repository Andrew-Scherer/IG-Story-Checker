"""
Models Package
Exposes all database models and provides initialization utilities
"""

from .base import BaseModel, db
from .profile import Profile
from .niche import Niche
from .batch import Batch, BatchProfile
from .story import StoryResult
from .settings import Proxy, SystemSettings

__all__ = [
    'db',
    'BaseModel',
    'Profile',
    'Niche',
    'Batch',
    'BatchProfile',
    'StoryResult',
    'Proxy',
    'SystemSettings'
]

def init_db():
    """Initialize database and create all tables"""
    db.create_all()

def drop_db():
    """Drop all database tables"""
    db.drop_all()

def reset_db():
    """Reset database by dropping and recreating all tables"""
    drop_db()
    init_db()

def seed_db():
    """Seed database with initial data"""
    # Create default system settings
    if not SystemSettings.query.get(1):
        settings = SystemSettings()
        settings.save()

    # TODO: Add any other necessary seed data
    # 1. Default niches
    # 2. Test profiles
    # 3. Sample proxies
