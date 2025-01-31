"""
Batch Model
Handles batch processing state and profile results
"""

import uuid
from datetime import datetime, UTC
from sqlalchemy import inspect
from flask import current_app
from .base import BaseModel, db

class Batch(BaseModel):
    """Batch processing model"""
    __tablename__ = 'batches'
    __table_args__ = {'extend_existing': True}

    # Primary fields
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    niche_id = db.Column(db.String(36), db.ForeignKey('niches.id'), nullable=False)
    status = db.Column(db.String(20), default='queued', nullable=False)
    position = db.Column(db.Integer, nullable=True)  # Queue position
    
    # Statistics
    total_profiles = db.Column(db.Integer, nullable=False)
    completed_profiles = db.Column(db.Integer, default=0)
    successful_checks = db.Column(db.Integer, default=0)
    failed_checks = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    niche = db.relationship('Niche', backref=db.backref('batches', lazy=True))
    profiles = db.relationship('BatchProfile', back_populates='batch', lazy='joined', cascade='all, delete-orphan')
    story_results = db.relationship('StoryResult', back_populates='batch', lazy=True)
    logs = db.relationship('BatchLog', back_populates='batch', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, niche_id, profile_ids):
        """Initialize a new batch"""
        self.niche_id = niche_id
        self.total_profiles = len(profile_ids)
        
        # Create BatchProfile records
        for profile_id in profile_ids:
            profile = BatchProfile(
                batch=self,
                profile_id=profile_id,
                status='pending'
            )
            self.profiles.append(profile)

    @property
    def completion_rate(self):
        """Calculate completion rate as percentage"""
        if self.total_profiles == 0:
            return 0.0
        return (self.completed_profiles / self.total_profiles) * 100.0

    def to_dict(self):
        """Convert batch to dictionary"""
        try:
            # Check if niche is loaded
            niche_dict = None
            if 'niche' in inspect(self).unloaded:
                db.session.refresh(self)
            if self.niche:
                niche_dict = self.niche.to_dict()
            
            # Get profiles with stories
            profiles_with_stories = [
                bp.profile.username for bp in self.profiles if bp.has_story
            ]
            
            return {
                'id': self.id,
                'niche_id': self.niche_id,
                'niche': niche_dict,
                'status': self.status,
                'position': self.position,
                'total_profiles': self.total_profiles,
                'completed_profiles': self.completed_profiles,
                'successful_checks': self.successful_checks,
                'failed_checks': self.failed_checks,
                'completion_rate': self.completion_rate,
                'profiles_with_stories': profiles_with_stories,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            }
        except Exception as e:
            current_app.logger.error(f"Error in batch.to_dict(): {str(e)}")
            raise

class BatchProfile(BaseModel):
    """Individual profile processing within a batch"""
    __tablename__ = 'batch_profiles'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    batch_id = db.Column(db.String(36), db.ForeignKey('batches.id'), nullable=False)
    profile_id = db.Column(db.String(36), db.ForeignKey('profiles.id'), nullable=False)
    proxy_id = db.Column(db.String(36), db.ForeignKey('proxies.id'), nullable=True)
    
    # Processing state
    status = db.Column(db.String(20), default='pending', nullable=False)
    has_story = db.Column(db.Boolean, default=False)
    error = db.Column(db.String(255), nullable=True)
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    batch = db.relationship('Batch', back_populates='profiles')
    profile = db.relationship('Profile', back_populates='batch_profiles')
    proxy = db.relationship('Proxy')

    def complete(self, has_story=False):
        """Mark profile as processed"""
        self.status = 'completed'
        self.has_story = has_story
        self.processed_at = datetime.now(UTC)
        
        # Update batch stats
        self.batch.completed_profiles += 1
        if has_story:
            self.batch.successful_checks += 1
        else:
            self.batch.failed_checks += 1
        
        # Auto-complete batch if all profiles done
        if self.batch.completed_profiles >= self.batch.total_profiles:
            self.batch.status = 'done'
            self.batch.position = None
            self.batch.completed_at = datetime.now(UTC)
        
        # Update profile stats
        self.profile.record_check(story_detected=has_story)

    def fail(self, error):
        """Mark profile as failed"""
        self.status = 'failed'
        self.error = str(error)
        self.processed_at = datetime.now(UTC)
        
        # Update batch stats
        self.batch.completed_profiles += 1
        self.batch.failed_checks += 1
        
        # Auto-complete batch if all profiles done
        if self.batch.completed_profiles >= self.batch.total_profiles:
            self.batch.status = 'done'
            self.batch.position = None
            self.batch.completed_at = datetime.now(UTC)

    def to_dict(self):
        """Convert batch profile to dictionary"""
        return {
            **super().to_dict(),
            'batch_id': self.batch_id,
            'profile_id': self.profile_id,
            'proxy_id': self.proxy_id,
            'status': self.status,
            'has_story': self.has_story,
            'error': self.error,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
