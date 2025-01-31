from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, db
import uuid

class BatchLog(BaseModel):
    __tablename__ = 'batch_logs'
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey('batches.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    event_type = Column(String(50), nullable=False)
    message = Column(String(500), nullable=False)
    profile_id = Column(String(36), ForeignKey('profiles.id'), nullable=True)
    proxy_id = Column(String(36), ForeignKey('proxies.id'), nullable=True)

    # Relationships
    batch = relationship('Batch', back_populates='logs')
    profile = relationship('Profile')
    proxy = relationship('Proxy')

    def __init__(self, batch_id, event_type, message, profile_id=None, proxy_id=None):
        self.id = str(uuid.uuid4())
        self.batch_id = batch_id
        self.event_type = event_type
        self.message = message
        self.profile_id = profile_id
        self.proxy_id = proxy_id

    def to_dict(self):
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'message': self.message,
            'profile_id': self.profile_id,
            'proxy_id': self.proxy_id
        }
