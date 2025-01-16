"""
Session Model
Manages Instagram session data and health metrics
"""

from datetime import datetime, UTC, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from models.base import Base, BaseModel, SoftDeleteMixin

class Session(Base, BaseModel, SoftDeleteMixin):
    """Instagram session with health tracking"""
    
    __tablename__ = 'sessions'
    
    # Maximum errors before disabling session
    MAX_ERRORS = 5
    
    # Status values
    STATUS_ACTIVE = 'active'
    STATUS_COOLDOWN = 'cooldown'
    STATUS_DISABLED = 'disabled'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Session data
    cookie = Column(String, unique=True, nullable=False)
    status = Column(
        Enum(STATUS_ACTIVE, STATUS_COOLDOWN, STATUS_DISABLED, name='session_status'),
        default=STATUS_ACTIVE,
        nullable=False
    )
    
    # Proxy relationship
    proxy_id = Column(Integer, ForeignKey('proxies.id'))
    proxy = relationship('Proxy', back_populates='sessions')
    
    # Health metrics
    total_checks = Column(Integer, default=0, nullable=False)
    successful_checks = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_check = Column(DateTime(timezone=True))
    cooldown_until = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Validation
    __table_args__ = (
        CheckConstraint('successful_checks <= total_checks', name='check_successful_checks'),
        CheckConstraint('error_count >= 0', name='check_error_count'),
    )
    
    @hybrid_property
    def success_rate(self) -> float:
        """Calculate success rate of story checks
        
        Returns:
            Success rate between 0 and 1
        """
        if self.total_checks == 0:
            return 1.0
        return self.successful_checks / self.total_checks
    
    def is_on_cooldown(self) -> bool:
        """Check if session is on cooldown
        
        Returns:
            True if on cooldown, False otherwise
        """
        if not self.cooldown_until:
            return False
        return datetime.now(UTC) < self.cooldown_until
    
    def set_cooldown(self, minutes: int = 15) -> None:
        """Set session cooldown period
        
        Args:
            minutes: Number of minutes to cooldown
        """
        self.status = self.STATUS_COOLDOWN
        self.cooldown_until = datetime.now(UTC) + timedelta(minutes=minutes)
    
    def record_check(self, success: bool) -> None:
        """Record result of story check
        
        Args:
            success: Whether check was successful
        """
        self.total_checks += 1
        if success:
            self.successful_checks += 1
        self.last_check = datetime.now(UTC)
    
    def record_error(self, error: str) -> None:
        """Record error and update status
        
        Args:
            error: Error message
        """
        self.error_count += 1
        
        # Disable if too many errors
        if self.error_count >= self.MAX_ERRORS:
            self.status = self.STATUS_DISABLED
    
    def reactivate(self) -> None:
        """Reactivate disabled session"""
        self.status = self.STATUS_ACTIVE
        self.error_count = 0
        self.cooldown_until = None
    
    def delete(self) -> None:
        """Soft delete session"""
        super().delete()
        self.status = self.STATUS_DISABLED
    
    @classmethod
    def get_active(cls):
        """Get active sessions query"""
        return cls.query.filter(
            cls.status == cls.STATUS_ACTIVE,
            cls.deleted_at.is_(None)
        )
    
    @classmethod
    def get_on_cooldown(cls):
        """Get sessions on cooldown query"""
        return cls.query.filter(
            cls.status == cls.STATUS_COOLDOWN,
            cls.deleted_at.is_(None)
        )
    
    @classmethod
    def get_disabled(cls):
        """Get disabled sessions query"""
        return cls.query.filter(
            cls.status == cls.STATUS_DISABLED,
            cls.deleted_at.is_(None)
        )
    
    def __repr__(self):
        return f'<Session {self.id} ({self.status})>'
