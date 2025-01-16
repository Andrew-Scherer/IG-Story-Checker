"""
Profile Model
Represents an Instagram profile in the system
"""

from datetime import datetime, UTC
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from .base import BaseModel

class Profile(BaseModel):
    """Model representing an Instagram profile.
    
    This is the central model that serves as the Master List for all Instagram profiles.
    It tracks profile status, story check history, and maintains relationships with niches
    and batch processing records.
    
    Attributes:
        id (str): UUID primary key
        username (str): Unique Instagram username
        url (str, optional): Profile URL
        niche_id (str, optional): Foreign key to associated niche
        status (str): Profile status (active/deleted/suspended)
        deleted_at (datetime, optional): Soft deletion timestamp
        total_checks (int): Total number of story checks performed
        total_detections (int): Number of successful story detections
        last_checked (datetime, optional): Last story check timestamp
        last_detected (datetime, optional): Last successful detection timestamp
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    __tablename__ = 'profiles'

    # Primary fields
    id = Column(String(36), primary_key=True)
    username = Column(String(30), unique=True, nullable=False)
    url = Column(String(255), nullable=True)
    niche_id = Column(String(36), ForeignKey('niches.id'), nullable=True)
    status = Column(String(20), nullable=False, default='active')
    deleted_at = Column(DateTime, nullable=True)

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
    )

    def __init__(self, username, url=None, niche=None, niche_id=None, status='active'):
        """Initialize a new Profile instance.
        
        Args:
            username (str): The Instagram username
            url (str, optional): The profile URL
            niche (Niche, optional): The niche this profile belongs to
            niche_id (str, optional): The ID of the niche this profile belongs to
            status (str, optional): Initial status, defaults to 'active'
            
        Raises:
            IntegrityError: If username is empty or None
            ValueError: If status is not one of VALID_STATUSES
        """
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

    def record_check(self, story_detected=False):
        """Record a story check attempt and its result.
        
        Updates check counters and timestamps based on the check result.
        
        Args:
            story_detected (bool): Whether a story was found during this check
        """
        self.total_checks += 1
        self.last_checked = datetime.now(UTC)
        
        if story_detected:
            self.total_detections += 1
            self.last_detected = self.last_checked

    def set_status(self, new_status):
        """Update the profile status.
        
        Args:
            new_status (str): New status value
            
        Raises:
            ValueError: If status is not one of VALID_STATUSES
        """
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        self.status = new_status
        self.updated_at = datetime.now(UTC)

    def soft_delete(self):
        """Soft delete the profile by marking it as deleted.
        
        Updates status to 'deleted' and sets deletion timestamp.
        """
        self.status = 'deleted'
        self.deleted_at = datetime.now(UTC)
        self.updated_at = self.deleted_at

    def reactivate(self):
        """Reactivate a deleted profile.
        
        Clears deleted status and timestamp.
        """
        self.status = 'active'
        self.deleted_at = None
        self.updated_at = datetime.now(UTC)

    @property
    def is_active(self):
        """Check if the profile is active.
        
        Returns:
            bool: True if status is 'active', False otherwise
        """
        return self.status == 'active'

    @property
    def detection_rate(self):
        """Calculate the success rate of story detections.
        
        Returns:
            float: Percentage of checks that detected a story (0-100)
        """
        if self.total_checks == 0:
            return 0.0
        return (self.total_detections / self.total_checks) * 100

    def to_dict(self):
        """Convert profile to dictionary.
        
        Returns:
            dict: Dictionary representation of profile with all fields
        """
        return {
            'id': self.id,
            'username': self.username,
            'url': self.url,
            'niche_id': self.niche_id,
            'status': self.status,
            'total_checks': self.total_checks,
            'total_detections': self.total_detections,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'last_detected': self.last_detected.isoformat() if self.last_detected else None,
            'detection_rate': self.detection_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }

    def __repr__(self):
        """String representation of the Profile.
        
        Returns:
            str: Profile representation with username and status
        """
        return f"<Profile(username='{self.username}', status='{self.status}')>"
