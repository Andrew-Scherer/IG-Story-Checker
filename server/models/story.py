"""
Story Result Model
Tracks detected Instagram stories and handles expiration
"""

import uuid
from datetime import datetime, timedelta
from .base import BaseModel, db

class StoryResult(BaseModel):
    """Story detection result model"""
    __tablename__ = 'story_results'

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    profile_id = db.Column(db.String(36), db.ForeignKey('profiles.id'), nullable=False)
    batch_id = db.Column(db.String(36), db.ForeignKey('batches.id'), nullable=False)
    
    # Detection information
    detected_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Optional metadata
    screenshot_url = db.Column(db.String(255), nullable=True)
    story_metadata = db.Column(db.JSON, nullable=True)  # Renamed from metadata to story_metadata
    
    # Relationships
    profile = db.relationship('Profile', back_populates='story_results')
    batch = db.relationship('Batch', backref=db.backref('story_results', lazy=True))

    def __init__(self, profile_id, batch_id, retention_hours=24):
        """Initialize a new story result"""
        self.profile_id = profile_id
        self.batch_id = batch_id
        self.detected_at = datetime.utcnow()
        self.expires_at = self.detected_at + timedelta(hours=retention_hours)

    @property
    def is_expired(self):
        """Check if story has expired"""
        return datetime.utcnow() > self.expires_at

    @classmethod
    def get_active(cls, niche_id=None):
        """Get active (non-expired) story results"""
        query = cls.query.filter(cls.expires_at > datetime.utcnow())
        
        if niche_id:
            query = query.join(cls.profile).filter_by(niche_id=niche_id)
            
        return query.order_by(cls.detected_at.desc()).all()

    @classmethod
    def cleanup_expired(cls):
        """Remove expired story results"""
        expired = cls.query.filter(cls.expires_at <= datetime.utcnow())
        count = expired.count()
        expired.delete()
        db.session.commit()
        return count

    @classmethod
    def get_stats_for_niche(cls, niche_id):
        """Get story statistics for a niche"""
        return db.session.query(
            db.func.count(cls.id).label('total'),
            db.func.count(db.distinct(cls.profile_id)).label('unique_profiles')
        ).join(cls.profile).filter(
            cls.profile.has(niche_id=niche_id),
            cls.expires_at > datetime.utcnow()
        ).first()

    def extend_expiration(self, hours=24):
        """Extend story expiration time"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.save()

    def add_metadata(self, data):
        """Add additional metadata to story result"""
        if self.story_metadata:
            self.story_metadata.update(data)
        else:
            self.story_metadata = data
        self.save()

    def to_dict(self):
        """Convert story result to dictionary"""
        return {
            **super().to_dict(),
            'profile_id': self.profile_id,
            'batch_id': self.batch_id,
            'detected_at': self.detected_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'screenshot_url': self.screenshot_url,
            'story_metadata': self.story_metadata,
            'is_expired': self.is_expired
        }

    def __repr__(self):
        """String representation"""
        return f'<StoryResult {self.profile_id} {self.detected_at}>'
