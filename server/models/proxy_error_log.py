"""Proxy Error Log Model"""

from datetime import datetime, UTC
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class ProxyErrorLog(BaseModel):
    """Model for logging proxy errors and state transitions"""

    __tablename__ = 'proxy_error_logs'
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    proxy_id = Column(String(36), ForeignKey('proxies.id'), nullable=True)
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    error_message = Column(Text, nullable=False)
    state_change = Column(Boolean, default=False)  # Was error state-changing
    transition_reason = Column(Text, nullable=True)  # Detailed reason for the state change
    recovery_time = Column(DateTime(timezone=True), nullable=True)  # When proxy-session pair became active again

    # Relationships
    proxy = relationship("Proxy", back_populates="error_logs")
    session = relationship("Session", back_populates="error_logs")

    def __init__(self, proxy_id=None, session_id=None, error_message=None, state_change=False, transition_reason=None, recovery_time=None):
        self.proxy_id = proxy_id
        self.session_id = session_id
        self.error_message = error_message
        self.state_change = state_change
        self.transition_reason = transition_reason
        self.recovery_time = recovery_time

    def to_dict(self):
        return {
            'id': self.id,
            'proxy_id': self.proxy_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message,
            'state_change': self.state_change,
            'transition_reason': self.transition_reason,
            'recovery_time': self.recovery_time.isoformat() if self.recovery_time else None,
        }
