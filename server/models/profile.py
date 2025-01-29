"""
Profile Model
Represents an Instagram profile in the system
"""

from datetime import datetime, UTC
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from .base import BaseModel

class Profile(BaseModel):
    """Model representing an Instagram profile."""
    
    __tablename__ = 'profiles'

    # Primary fields
    id = Column(String(36), primary_key=True)
    username = Column(String(30), unique=True, nullable=False)
    url = Column(String(255), nullable=True)
    niche_id = Column(String(36), ForeignKey('niches.id'), nullable=True)
    status = Column(String(20), nullable=False, default='active')

    # Story status fields
    active_story = Column(Boolean, nullable=False, default=False)
    last_story_detected = Column(DateTime(timezone=True), nullable=True)

    # Valid status values
    VALID_STATUSES = ['active', 'deleted', 'suspended']

    # Tracking fields
    total_checks = Column(Integer, default=0, nullable=False)
    total_detections = Column(Integer, default=0, nullable=False)
    last_checked = Column(DateTime, nullable=True)
    last_detected = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    niche = relationship("Niche", back_populates="profiles")
    batch_profiles = relationship("BatchProfile", back_populates="profile")
    story_results = relationship("StoryResult", back_populates="profile")

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_profile_username', 'username'),
        Index('idx_profile_status', 'status'),
        Index('idx_profile_niche', 'niche_id'),
        Index('idx_profile_last_checked', 'last_checked'),
        Index('idx_profile_active_story', 'active_story'),
    )

    def __init__(self, username, url=None, niche=None, niche_id=None, status='active'):
        """Initialize a new Profile instance."""
        if not username or not username.strip():
            raise IntegrityError("Username cannot be empty", None, None)
            
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
            
        self.id = str(uuid.uuid4())
        self.username = username
        self.url = url
        if niche is not None:
            self.niche = niche
        elif niche_id is not None:
            self.niche_id = niche_id
        self.status = status
        self.total_checks = 0
        self.total_detections = 0
        self.active_story = False

    def record_check(self, story_detected=False):
        """Record a story check attempt and its result."""
        self.total_checks += 1
        self.last_checked = datetime.now(UTC)
        self.active_story = story_detected
        
        if story_detected:
            self.total_detections += 1
            self.last_detected = self.last_checked
            self.last_story_detected = self.last_checked

    def set_status(self, new_status):
        """Update the profile status."""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        self.status = new_status
        self.updated_at = datetime.now(UTC)

    def soft_delete(self):
        """Soft delete the profile by marking it as deleted."""
        self.status = 'deleted'
        self.updated_at = datetime.now(UTC)

    def reactivate(self):
        """Reactivate a deleted profile."""
        self.status = 'active'
        self.updated_at = datetime.now(UTC)

    @property
    def is_active(self):
        """Check if the profile is active."""
        return self.status == 'active'

    @property
    def detection_rate(self):
        """Calculate the success rate of story detections."""
        if self.total_checks == 0:
            return 0.0
        return (self.total_detections / self.total_checks) * 100

    def to_dict(self):
        """Convert profile to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'url': self.url,
            'niche_id': self.niche_id,
            'niche': self.niche.name if self.niche else None,
            'status': self.status,
            'active_story': self.active_story,
            'last_story_detected': self.last_story_detected.isoformat() if self.last_story_detected else None,
            'total_checks': self.total_checks,
            'total_detections': self.total_detections,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'last_detected': self.last_detected.isoformat() if self.last_detected else None,
            'detection_rate': self.detection_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """String representation of the Profile."""
        return f"<Profile(username='{self.username}', status='{self.status}')>"
