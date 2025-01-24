from sqlalchemy import Column, String, Integer, Boolean, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel, db
from .proxy_error_log import ProxyErrorLog
import uuid
from enum import Enum as PyEnum
from datetime import datetime, UTC

class ProxyStatus(PyEnum):
    """Proxy status states"""
    ACTIVE = "active"
    DISABLED = "disabled"
    RATE_LIMITED = "rate_limited"

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
    avg_response_time = Column(Integer, default=0)  # in milliseconds
    last_error = Column(String)
    last_success = Column(DateTime(timezone=True))
    
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
    
    # One-to-many relationship with ProxyErrorLog
    error_logs = relationship(
        "ProxyErrorLog",
        back_populates="proxy",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(ProxyErrorLog.timestamp)"
    )
    
    # Unique constraint for ip+port combination
    __table_args__ = (
        UniqueConstraint('ip', 'port', name='uix_proxy_ip_port'),
    )
    
    def __str__(self):
        return f"{self.ip}:{self.port}:{self.username}:{self.password}"
    
    def __repr__(self):
        return f"<Proxy {self.ip}:{self.port}>"
    
    _status = Column('status', String(20), default=ProxyStatus.ACTIVE.value)

    @property
    def status(self) -> ProxyStatus:
        """Get proxy status"""
        return ProxyStatus(self._status)

    @status.setter
    def status(self, value: ProxyStatus):
        """Set proxy status"""
        if isinstance(value, ProxyStatus):
            self._status = value.value
        elif isinstance(value, str) and value in [e.value for e in ProxyStatus]:
            self._status = value
        else:
            raise ValueError(f"Invalid status value: {value}")
    
    def record_request(self, success=True, response_time=None, error_msg=None):
        """Record a request attempt and its result.
        
        Args:
            success (bool): Whether the request was successful
            response_time (int, optional): Response time in milliseconds
            error_msg (str, optional): Error message if request failed
        """
        now = datetime.now(UTC)
        self.total_requests += 1
        self.requests_this_hour += 1
        self.last_used = now
        
        if not success:
            self.failed_requests += 1
            self.error_count += 1
            if error_msg:
                self.last_error = error_msg
                # Create a new ProxyErrorLog entry
                error_log = ProxyErrorLog(proxy_id=self.id, error_message=error_msg)
                db.session.add(error_log)
        else:
            self.error_count = 0  # Reset error count on success
            self.last_success = now
            
            # Update average response time
            if response_time is not None:
                if self.avg_response_time == 0:
                    self.avg_response_time = response_time
                else:
                    # Weighted average: 70% old value, 30% new value
                    self.avg_response_time = int(0.7 * self.avg_response_time + 0.3 * response_time)
            
        self.updated_at = now
        
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
            'error_count': self.error_count,
            'avg_response_time': self.avg_response_time,
            'last_error': self.last_error,
            'last_success': self.last_success.isoformat() if self.last_success else None
        }
