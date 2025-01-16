"""
Niche Model
Represents a category for organizing profiles
"""

import uuid
from sqlalchemy import Column, String, Integer, UniqueConstraint, select
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError
from .base import BaseModel, db

class Niche(BaseModel):
    """Model representing a niche category.
    
    Niches are used to organize profiles into categories and support
    reordering for visual organization in the UI.
    """
    
    __tablename__ = 'niches'

    # Primary fields
    id = Column(String(36), primary_key=True)
    name = Column(String(50), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    daily_story_target = Column(Integer, nullable=False, default=10)

    # Ensure name uniqueness
    __table_args__ = (
        UniqueConstraint('name', name='uq_niche_name'),
    )

    # Relationships
    profiles = relationship(
        "Profile",
        back_populates="niche",
        passive_deletes=False  # Profiles remain when niche is deleted
    )

    def __init__(self, name, display_order=None, daily_story_target=10):
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
        self.display_order = display_order if display_order is not None else 0
        self.daily_story_target = daily_story_target

    @classmethod
    def reorder(cls, niche_ids):
        """Reorder niches based on list of IDs.
        
        Args:
            niche_ids (list): List of niche IDs in desired order
        """
        for index, niche_id in enumerate(niche_ids):
            niche = db.session.get(cls, niche_id)
            if niche:
                niche.display_order = index

    @classmethod
    def get_ordered(cls):
        """Get all niches in display order.
        
        Returns:
            list: Niches ordered by display_order
        """
        stmt = select(cls).order_by(cls.display_order.asc())
        return db.session.execute(stmt).scalars().all()

    def to_dict(self):
        """Convert niche to dictionary.
        
        Returns:
            dict: Dictionary representation of niche including base fields
        """
        return {
            'id': self.id,
            'name': self.name,
            'display_order': self.display_order,
            'daily_story_target': self.daily_story_target,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def __repr__(self):
        """String representation of the Niche."""
        return f"<Niche(name='{self.name}')>"
