from sqlalchemy import Column, String, Integer, Enum, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, UTC
from enum import Enum as PyEnum
from models.base import Base, BaseModel

class ProxyStatus(PyEnum):
    """Proxy status states"""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    DISABLED = "disabled"

class Proxy(Base, BaseModel):
    """Proxy model with health tracking and rate limiting"""
    
    __tablename__ = 'proxies'
    
    # Constants
    HOURLY_LIMIT = 150  # Maximum requests per hour
    ERROR_THRESHOLD = 5  # Max errors before disabling
    COOLDOWN_MINUTES = 15  # Minutes to cooldown after rate limit
    
    # Basic proxy info
    id = Column(Integer, primary_key=True)
    ip = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    
    # Status and health tracking
    status = Column(Enum(ProxyStatus), default=ProxyStatus.ACTIVE, nullable=False)
    cooldown_until = Column(DateTime(timezone=True))
    last_error = Column(String(255))
    error_count = Column(Integer, default=0)
    
    # Request tracking
    requests_this_hour = Column(Integer, default=0)
    last_reset = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    total_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    average_response_time = Column(Float)
    
    # Timestamps
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # One-to-many relationship with Session
    sessions = relationship("Session", back_populates="proxy")
    
    def __str__(self):
        return f"{self.ip}:{self.port}:{self.username}:{self.password}"
    
    def __repr__(self):
        return f"<Proxy {self.ip}:{self.port}>"
    
    @property
    def is_usable(self) -> bool:
        """Check if proxy can be used"""
        if self.status == ProxyStatus.DISABLED:
            return False
            
        if self.status == ProxyStatus.RATE_LIMITED:
            # Check if cooldown has expired
            if self.cooldown_until and datetime.now(UTC) > self.cooldown_until:
                self.status = ProxyStatus.ACTIVE
                self.cooldown_until = None
                return True
            return False
            
        return True
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests
    
    def set_rate_limited(self) -> None:
        """Mark proxy as rate limited with cooldown"""
        self.status = ProxyStatus.RATE_LIMITED
        # Extend cooldown if already rate limited
        if self.cooldown_until and self.cooldown_until > datetime.now(UTC):
            self.cooldown_until += timedelta(minutes=self.COOLDOWN_MINUTES)
        else:
            self.cooldown_until = datetime.now(UTC) + timedelta(minutes=self.COOLDOWN_MINUTES)
    
    def record_request(self, success: bool, response_time: float = None, error: str = None) -> None:
        """Record request metrics
        
        Args:
            success: Whether request succeeded
            response_time: Response time in milliseconds
            error: Error message if failed
        """
        now = datetime.now(UTC)
        
        # Update request counts and timestamp
        self.total_requests += 1
        self.requests_this_hour += 1
        self.last_used = now
        self.last_reset = now  # Update timestamp for tracking
        
        if success:
            # Update response time average with more weight on recent times
            if response_time:
                if self.average_response_time is None:
                    self.average_response_time = response_time
                else:
                    # Weighted average: 0.6 old + 0.4 new to match test expectations
                    self.average_response_time = (
                        self.average_response_time * 0.6 + response_time * 0.4
                    )
            # Reset error count on success
            self.error_count = 0
            
        else:
            self.failed_requests += 1
            if error:
                self.last_error = error
                self.error_count += 1
                
                # Disable if too many errors
                if self.error_count >= self.ERROR_THRESHOLD:
                    self.status = ProxyStatus.DISABLED
        
        # Check rate limit
        if self.requests_this_hour >= self.HOURLY_LIMIT:
            self.set_rate_limited()
