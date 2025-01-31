"""Session Model
Manages Instagram session data"""

from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel, db
import uuid

class Session(BaseModel):
    """Instagram session model"""
    
    __tablename__ = 'sessions'
    
    # Status values
    STATUS_ACTIVE = 'active'
    STATUS_DISABLED = 'disabled'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Session data
    session = Column(String, unique=True, nullable=False)
    status = Column(
        Enum(STATUS_ACTIVE, STATUS_DISABLED, name='session_status'),
        default=STATUS_ACTIVE,
        nullable=False
    )
    
    # Proxy relationship
    proxy_id = Column(String(36), ForeignKey('proxies.id'), unique=True)  # One session per proxy
    proxy = relationship("Proxy", back_populates="sessions")
    
    # Error logs relationship
    error_logs = relationship("ProxyErrorLog", back_populates="session")
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            **super().to_dict(),
            'session': self.session,
            'status': self.status,
            'proxy_id': self.proxy_id
        }

    def __repr__(self):
        return f'<Session {self.id} ({self.status})>'
        
    def is_valid(self) -> bool:
        """Check if session is valid (active)"""
        return self.status == self.STATUS_ACTIVE
