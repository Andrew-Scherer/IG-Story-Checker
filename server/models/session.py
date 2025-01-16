"""
Session Model
Manages Instagram session data
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from models.base import Base, BaseModel

class Session(Base, BaseModel):
    """Instagram session model"""
    
    __tablename__ = 'sessions'
    
    # Status values
    STATUS_ACTIVE = 'active'
    STATUS_DISABLED = 'disabled'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Session data
    session = Column(String, unique=True, nullable=False)
    status = Column(
        Enum(STATUS_ACTIVE, STATUS_DISABLED, name='session_status'),
        default=STATUS_ACTIVE,
        nullable=False
    )
    
    # Proxy relationship
    proxy_id = Column(Integer, ForeignKey('proxies.id'), unique=True)  # One session per proxy
    proxy = relationship('Proxy', back_populates='sessions')
    
    def __repr__(self):
        return f'<Session {self.id} ({self.status})>'
