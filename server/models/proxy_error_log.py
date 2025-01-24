"""Proxy Error Log Model"""

from datetime import datetime, UTC
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class ProxyErrorLog(BaseModel):
    """Model for logging proxy errors"""

    __tablename__ = 'proxy_error_logs'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    proxy_id = Column(String(36), ForeignKey('proxies.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    error_message = Column(Text, nullable=False)

    # Relationships
    proxy = relationship("Proxy", back_populates="error_logs")

    def __init__(self, proxy_id, error_message):
        self.proxy_id = proxy_id
        self.error_message = error_message

    def to_dict(self):
        return {
            'id': self.id,
            'proxy_id': self.proxy_id,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message,
        }
