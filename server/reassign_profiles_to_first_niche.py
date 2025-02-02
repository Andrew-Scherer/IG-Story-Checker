"""
Script to reassign profiles from a deleted niche to the first available niche
"""

import sys
from sqlalchemy import select
from flask import Flask
from config import DevelopmentConfig
from extensions import db
from models.niche import Niche
from models.profile import Profile

def reassign_profiles(niche_id_to_delete):
    """
    Reassign all profiles from the specified niche to the first available niche
    
    Args:
        niche_id_to_delete (str): ID of the niche being deleted
    """
    try:
        # Get the niche being deleted
        niche_to_delete = db.session.execute(
            select(Niche).where(Niche.id == niche_id_to_delete)
        ).scalar()
        
        if not niche_to_delete:
            print(f"Error: Niche with ID {niche_id_to_delete} not found")
            return False
            
        # Get first available niche that's not being deleted
        first_niche = db.session.execute(
            select(Niche)
            .where(Niche.id != niche_id_to_delete)
            .order_by(Niche.order.asc())
        ).scalar()
        
        if not first_niche:
            print("Error: No other niches available to reassign profiles to")
            return False
            
        # Get all profiles from the niche being deleted
        profiles_to_reassign = db.session.execute(
            select(Profile).where(Profile.niche_id == niche_id_to_delete)
        ).scalars().all()
        
        if not profiles_to_reassign:
            print(f"No profiles found in niche {niche_to_delete.name}")
            return True
            
        print(f"Found {len(profiles_to_reassign)} profiles to reassign")
        print(f"Reassigning profiles from '{niche_to_delete.name}' to '{first_niche.name}'")
        
        # Update all profiles to use the first niche
        for profile in profiles_to_reassign:
            profile.niche_id = first_niche.id
            profile.niche = first_niche
            print(f"Reassigned profile {profile.username}")
            
        db.session.commit()
        print("Successfully reassigned all profiles")
        return True
        
    except Exception as e:
        print(f"Error reassigning profiles: {str(e)}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python reassign_profiles_to_first_niche.py <niche_id>")
        sys.exit(1)
        
    niche_id = sys.argv[1]
    app = create_app()
    
    with app.app_context():
        success = reassign_profiles(niche_id)
        sys.exit(0 if success else 1)