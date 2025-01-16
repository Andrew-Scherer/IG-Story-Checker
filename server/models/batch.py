"""
Batch Models
Handles batch processing state and profile results
"""

import uuid
from datetime import datetime, UTC
from sqlalchemy import inspect
from .base import BaseModel, db

class Batch(BaseModel):
    """Batch processing model
    
    Manages the state and statistics of a batch story check operation.
    Each batch is associated with a niche and contains multiple profiles
    to be processed.
    """
    __tablename__ = 'batches'

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Batch information
    niche_id = db.Column(db.String(36), db.ForeignKey('niches.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    
    # Timing
    start_time = db.Column(db.DateTime(timezone=True), nullable=True)
    end_time = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Statistics
    total_profiles = db.Column(db.Integer, default=0)
    completed_profiles = db.Column(db.Integer, default=0)
    successful_checks = db.Column(db.Integer, default=0)
    failed_checks = db.Column(db.Integer, default=0)
    
    # Relationships
    niche = db.relationship('Niche', backref=db.backref('batches', lazy=True))
    profiles = db.relationship('BatchProfile', back_populates='batch', lazy=True)

    def __init__(self, niche_id):
        """Initialize a new batch"""
        self.niche_id = niche_id

    def start(self, session=None):
        """Start batch processing"""
        self.status = 'running'
        self.start_time = datetime.now(UTC)
        self.save(session=session)

    def complete(self, session=None):
        """Mark batch as completed"""
        self.status = 'completed'
        self.end_time = datetime.now(UTC)
        self.save(session=session)

    def fail(self, reason=None, session=None):
        """Mark batch as failed"""
        self.status = 'failed'
        self.end_time = datetime.now(UTC)
        # TODO: Log failure reason
        self.save(session=session)

    @classmethod
    def get_by_id(cls, id):
        """Get batch by ID"""
        return db.session.get(cls, id)

    def update_stats(self, session=None):
        """Update batch statistics"""
        session = session or db.session

        stats = session.query(
            db.func.count(BatchProfile.id),
            db.func.sum(
                db.case(
                    (BatchProfile.status == 'completed', 1),
                    else_=0
                )
            ),
            db.func.sum(
                db.case(
                    (BatchProfile.has_story == True, 1),
                    else_=0
                )
            ),
            db.func.sum(
                db.case(
                    (BatchProfile.status == 'failed', 1),
                    else_=0
                )
            )
        ).filter(BatchProfile.batch_id == self.id).first()

        self.total_profiles = stats[0] or 0
        self.completed_profiles = stats[1] or 0
        self.successful_checks = stats[2] or 0
        self.failed_checks = stats[3] or 0
        self.save(session=session)

    @classmethod
    def get_active_for_niche(cls, niche_id, session=None):
        """Get active batch for niche if exists"""
        session = session or db.session
        return session.query(cls).filter_by(
            niche_id=niche_id,
            status='running'
        ).first()

    def to_dict(self):
        """Convert batch to dictionary"""
        return {
            **super().to_dict(),
            'niche_id': self.niche_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_profiles': self.total_profiles,
            'completed_profiles': self.completed_profiles,
            'successful_checks': self.successful_checks,
            'failed_checks': self.failed_checks
        }

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
    
    # Processing state
    status = db.Column(db.String(20), default='pending', nullable=False)
    has_story = db.Column(db.Boolean, default=False)
    error = db.Column(db.String(255), nullable=True)
    
    # Timing
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    batch = db.relationship('Batch', back_populates='profiles')
    profile = db.relationship('Profile', back_populates='batch_profiles')

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
        self.batch.update_stats(session=session)
        
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
        self.batch.update_stats(session=session)

    def to_dict(self):
        """Convert batch profile to dictionary"""
        return {
            **super().to_dict(),
            'batch_id': self.batch_id,
            'profile_id': self.profile_id,
            'status': self.status,
            'has_story': self.has_story,
            'error': self.error,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
