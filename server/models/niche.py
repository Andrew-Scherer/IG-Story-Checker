"""
Niche Model
Represents a category for organizing profiles
"""

import uuid
from sqlalchemy import Column, String, Integer, UniqueConstraint, select, event, func
from sqlalchemy.orm import relationship, reconstructor
from sqlalchemy.exc import IntegrityError
from .base import BaseModel, db
from datetime import datetime, timezone

class Niche(BaseModel):
    """Model representing a niche category.
    
    Niches are used to organize profiles into categories and support
    reordering for visual organization in the UI.
    """
    
    __tablename__ = 'niches'

    # Primary fields
    id = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    daily_story_target = Column(Integer, nullable=False, default=10)

    # Table arguments
    __table_args__ = (
        UniqueConstraint('name', name='uq_niche_name'),
        {'extend_existing': True}
    )

    # Relationships
    profiles = relationship(
        "Profile",
        back_populates="niche",
        passive_deletes=False  # Profiles remain when niche is deleted
    )

    def __init__(self, name, order=None, daily_story_target=10):
        """Initialize a new niche.
        
        Args:
            name (str): The niche name
            display_order (int, optional): Display position in UI
            daily_story_target (int, optional): Target number of stories per day
            
        Raises:
            IntegrityError: If name is empty or None
        """
        if not name or not name.strip():
            raise IntegrityError("Niche name cannot be empty", None, None)
            
        self.id = str(uuid.uuid4())
        self.name = name
        self.order = order if order is not None else 0
        self.daily_story_target = daily_story_target
        self._update_timestamp()

    @classmethod
    def get_ordered(cls, session=None):
        """Get all niches with profile counts in a single query.
        
        Args:
            session: SQLAlchemy session to use (optional)
                    If not provided, uses the default db.session
        
        Returns:
            list: Niches ordered by display_order with profile counts
        """
        from models.profile import Profile
        session = session or db.session
        
        # Create subquery to count profiles per niche
        profile_counts = (
            session.query(
                Profile.niche_id,
                func.count(Profile.id).label('profile_count')
            )
            .group_by(Profile.niche_id)
            .subquery()
        )
        
        # Join with profile counts in main query
        results = (
            session.query(
                cls,
                func.coalesce(profile_counts.c.profile_count, 0).label('_profile_count')
            )
            .outerjoin(profile_counts, cls.id == profile_counts.c.niche_id)
            .order_by(cls.order.asc())
            .all()
        )
        
        # Attach counts to niche objects
        for niche, count in results:
            niche._profile_count = count
            
        return [niche for niche, _ in results]

    def to_dict(self):
        """Convert niche to dictionary.
        
        Returns:
            dict: Dictionary representation of niche including base fields
        """
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'daily_story_target': self.daily_story_target,
            'profile_count': getattr(self, '_profile_count', 0),  # Use cached count
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """String representation of the Niche."""
        return f"<Niche(name='{self.name}')>"

    @reconstructor
    def init_on_load(self):
        self._update_timestamp()

    def _update_timestamp(self):
        if hasattr(self, 'updated_at'):
            self.updated_at = datetime.now(timezone.utc)

@event.listens_for(Niche, 'before_update')
def receive_before_update(mapper, connection, target):
    target._update_timestamp()
