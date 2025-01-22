from sqlalchemy import Column, String, Integer, Boolean, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel, db
import uuid
from enum import Enum as PyEnum
from datetime import datetime, UTC

class ProxyStatus(PyEnum):
    """Proxy status states"""
    ACTIVE = "active"
    DISABLED = "disabled"

class Proxy(BaseModel):
    """Proxy model"""
    
    __tablename__ = 'proxies'
    
    # Basic proxy info
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ip = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255))
    password = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Request tracking
    total_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    requests_this_hour = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    rate_limited = Column(Boolean, default=False)
    last_used = Column(DateTime(timezone=True))
    
    # Rate limiting
    HOURLY_LIMIT = 150  # Maximum requests per hour
    
    # One-to-many relationship with Session
    sessions = relationship(
        "Session", 
        back_populates="proxy", 
        lazy="dynamic",
        cascade="all, delete-orphan",
        single_parent=True
    )
    
    # Unique constraint for ip+port combination
    __table_args__ = (
        UniqueConstraint('ip', 'port', name='uix_proxy_ip_port'),
    )
    
    def __str__(self):
        return f"{self.ip}:{self.port}:{self.username}:{self.password}"
    
    def __repr__(self):
        return f"<Proxy {self.ip}:{self.port}>"
    
    @property
    def status(self) -> ProxyStatus:
        """Get proxy status"""
        return ProxyStatus.ACTIVE if self.is_active else ProxyStatus.DISABLED
    
    def record_request(self, success=True, response_time=None):
        """Record a request attempt and its result.
        
        Args:
            success (bool): Whether the request was successful
            response_time (int, optional): Response time in milliseconds
        """
        self.total_requests += 1
        self.requests_this_hour += 1
        
        if not success:
            self.failed_requests += 1
            self.error_count += 1
        else:
            self.error_count = 0  # Reset error count on success
            
        self.updated_at = datetime.now(UTC)
        
    def reset_hourly_count(self):
        """Reset the hourly request counter."""
        self.requests_this_hour = 0
        self.updated_at = datetime.now(UTC)
        
    def to_dict(self):
        """Convert proxy to dictionary"""
        return {
            **super().to_dict(),
            'ip': self.ip,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'is_active': self.is_active,
            'status': self.status.value,
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'requests_this_hour': self.requests_this_hour,
            'error_count': self.error_count
        }
