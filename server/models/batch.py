"""
Batch Models
Handles batch processing state and profile results
"""

import uuid
from datetime import datetime, UTC
from sqlalchemy import inspect
from flask import current_app
from .base import BaseModel, db
from .batch_log import BatchLog

class Batch(BaseModel):
    """Batch processing model
    
    Manages the state and statistics of a batch story check operation.
    Each batch is associated with a niche and contains multiple profiles
    to be processed.

    Status values:
    - queued: Initial state, waiting to be processed
    - in_progress: Currently being processed
    - paused: Processing temporarily stopped, can be resumed
    - done: Processing completed
    """
    __tablename__ = 'batches'

    # Primary fields
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    niche_id = db.Column(db.String(36), db.ForeignKey('niches.id'), nullable=False)
    status = db.Column(db.String(20), default='queued', nullable=False)
    total_profiles = db.Column(db.Integer, nullable=False)
    completed_profiles = db.Column(db.Integer, default=0)
    successful_checks = db.Column(db.Integer, default=0)
    failed_checks = db.Column(db.Integer, default=0)
    queue_position = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    niche = db.relationship('Niche', backref=db.backref('batches', lazy=True))
    profiles = db.relationship('BatchProfile', back_populates='batch', lazy='joined', cascade='all, delete-orphan')
    story_results = db.relationship('StoryResult', back_populates='batch', cascade='all, delete-orphan')
    logs = db.relationship('BatchLog', back_populates='batch', lazy=True, cascade='all, delete-orphan')

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

    def preserve_state(self):
        """Calculate and preserve batch state"""
        # Calculate state from profiles
        self.completed_profiles = len([bp for bp in self.profiles if bp.status in ['completed', 'failed']])
        self.successful_checks = len([bp for bp in self.profiles if bp.status == 'completed' and bp.has_story])
        self.failed_checks = len([bp for bp in self.profiles if bp.status in ['failed']])
        
        # Save state to database
        db.session.commit()
        
        # Log state preservation
        current_app.logger.info(
            f'Preserved batch state: {self.completed_profiles} completed, '
            f'{self.successful_checks} successful, {self.failed_checks} failed'
        )

    def to_dict(self):
        """Convert batch to dictionary"""
        try:
            # Check if niche is loaded before accessing
            niche_dict = None
            if 'niche' in inspect(self).unloaded:
                db.session.refresh(self)
            if self.niche:
                try:
                    niche_dict = self.niche.to_dict()
                except Exception as e:
                    current_app.logger.error(f"Error converting niche to dict for batch {self.id}: {str(e)}")
            
            # Get list of profile usernames with stories found
            profiles_with_stories = [
                bp.profile.username for bp in self.profiles if bp.has_story
            ]
            
            return {
                'id': self.id,
                'niche_id': self.niche_id,
                'niche': niche_dict,
                'status': self.status,
                'total_profiles': self.total_profiles,
                'completed_profiles': self.completed_profiles,
                'successful_checks': self.successful_checks,
                'failed_checks': self.failed_checks,
                'queue_position': self.queue_position,
                'completion_rate': self.completion_rate,
                'profiles_with_stories': profiles_with_stories,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            }
        except Exception as e:
            current_app.logger.error(f"Error in batch.to_dict(): {str(e)}")
            raise

    @classmethod
    def get_by_id(cls, id):
        """Get batch by ID"""
        return db.session.get(cls, id)

    def record_check(self, has_story=False, session=None):
        """Record a story check result"""
        session = session or db.session
        
        self.completed_profiles += 1
        if has_story:
            self.successful_checks += 1
        else:
            self.failed_checks += 1
        
        if self.completed_profiles >= self.total_profiles:
            self.status = 'done'
            self.queue_position = None  # Clear queue position when done
            self.completed_at = datetime.now(UTC)  # Set completion time
        
        self.save(session=session)

class BatchProfile(BaseModel):
    """Individual profile processing within a batch
    
    Tracks the processing state and results for a single profile
    within a batch operation.
    """
    __tablename__ = 'batch_profiles'

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    batch_id = db.Column(db.String(36), db.ForeignKey('batches.id'), nullable=False)
    profile_id = db.Column(db.String(36), db.ForeignKey('profiles.id'), nullable=False)
    proxy_id = db.Column(db.String(36), db.ForeignKey('proxies.id'), nullable=True)
    session_id = db.Column(db.String(36), db.ForeignKey('sessions.id'), nullable=True)
    
    # Processing state
    status = db.Column(db.String(20), default='pending', nullable=False)
    has_story = db.Column(db.Boolean, default=False)
    error = db.Column(db.String(255), nullable=True)
    
    # Timing
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    batch = db.relationship('Batch', back_populates='profiles')
    profile = db.relationship('Profile', back_populates='batch_profiles')
    proxy = db.relationship('Proxy')
    session = db.relationship('Session')

    def complete(self, has_story=False, session=None):
        """Mark profile as processed"""
        session = session or db.session
        
        # Get the session this instance is already attached to
        instance_state = inspect(self)
        if instance_state.session_id:
            session = instance_state.session

        self.status = 'completed'
        self.has_story = has_story
        self.processed_at = datetime.now(UTC)
        self.save(session=session)
        
        # Update batch stats
        self.batch.record_check(has_story=has_story, session=session)
        
        # Update profile stats
        self.profile.record_check(story_detected=has_story)
        self.profile.save(session=session)

    def fail(self, error, session=None):
        """Mark profile as failed"""
        session = session or db.session
        
        # Get the session this instance is already attached to
        instance_state = inspect(self)
        if instance_state.session_id:
            session = instance_state.session

        self.status = 'failed'
        self.error = str(error)
        self.processed_at = datetime.now(UTC)
        self.save(session=session)
        
        # Update batch stats
        self.batch.record_check(has_story=False, session=session)

    def to_dict(self):
        """Convert batch profile to dictionary"""
        return {
            **super().to_dict(),
            'batch_id': self.batch_id,
            'profile_id': self.profile_id,
            'proxy_id': self.proxy_id,
            'session_id': self.session_id,
            'status': self.status,
            'has_story': self.has_story,
            'error': self.error,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
