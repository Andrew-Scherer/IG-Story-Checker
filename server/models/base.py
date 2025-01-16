"""
Base Model
Provides common functionality for all models
"""

from datetime import datetime, UTC
from sqlalchemy import inspect, Column, DateTime, MetaData, Integer
from sqlalchemy.orm import declarative_base, declared_attr
from app import db

# Create shared metadata instance
metadata = MetaData()

# Create declarative base with shared metadata
Base = declarative_base(metadata=metadata)

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    deleted_at = Column(DateTime(timezone=True))
    
    def delete(self):
        """Soft delete the record"""
        self.deleted_at = datetime.now(UTC)
    
    @classmethod
    def query(cls):
        """Query excluding soft-deleted records"""
        return db.session.query(cls).filter(cls.deleted_at.is_(None))
    
    @classmethod
    def with_deleted(cls):
        """Query including soft-deleted records"""
        return db.session.query(cls)

class BaseModel:
    """Abstract base model class
    
    Provides common functionality for all models including:
    - Automatic timestamp tracking (created_at, updated_at)
    - Session-aware save/delete operations
    - Basic serialization
    """
    @declared_attr
    def __tablename__(cls):
        """Generate tablename from class name"""
        return cls.__name__.lower() + 's'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def save(self, session=None):
        """Save the model instance
        
        Args:
            session: SQLAlchemy session to use (optional)
                    If not provided, uses the default db.session
        
        Returns:
            self: The saved model instance
        """
        session = session or db.session
        
        # Get the session this instance is already attached to, if any
        instance_state = inspect(self)
        if instance_state.session_id:
            # If already in a session, use that session
            instance_session = instance_state.session
            instance_session.add(self)
            instance_session.commit()
        else:
            # Otherwise use the provided/default session
            session.add(self)
            session.commit()
        return self

    def delete(self, session=None):
        """Delete the model instance
        
        Args:
            session: SQLAlchemy session to use (optional)
                    If not provided, uses the default db.session
        """
        session = session or db.session
        
        # Get the session this instance is already attached to, if any
        instance_state = inspect(self)
        if instance_state.session_id:
            # If already in a session, use that session
            instance_session = instance_state.session
            instance_session.delete(self)
            instance_session.commit()
        else:
            # Otherwise use the provided/default session
            session.delete(self)
            session.commit()

    @classmethod
    def get_by_id(cls, id, session=None):
        """Get a record by ID
        
        Args:
            id: The record ID
            session: SQLAlchemy session to use (optional)
        
        Returns:
            Model instance if found, None otherwise
        """
        session = session or db.session
        return session.query(cls).get(id)

    def to_dict(self):
        """Convert model to dictionary
        
        Returns:
            dict: Dictionary representation of model
        """
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
