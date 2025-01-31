from app import db
from models.profile import Profile
from models.niche import Niche

def import_test_profiles():
    """Import test profiles with specific niche assignments"""
    print("Importing test profiles...")
    
    # Get the niches
    golf_niche = db.session.query(Niche).filter(Niche.name == 'Golf').first()
    hunting_niche = db.session.query(Niche).filter(Niche.name == 'Hunting').first()
    
    if not golf_niche or not hunting_niche:
        print("Error: Required niches not found")
        return
        
    # Test profiles for Golf niche
    golf_profiles = [
        Profile(username="golf_user_1", niche_id=golf_niche.id),
        Profile(username="golf_user_2", niche_id=golf_niche.id),
        Profile(username="golf_user_3", niche_id=golf_niche.id)
    ]
    
    # Test profiles for Hunting niche
    hunting_profiles = [
        Profile(username="hunting_user_1", niche_id=hunting_niche.id),
        Profile(username="hunting_user_2", niche_id=hunting_niche.id),
        Profile(username="hunting_user_3", niche_id=hunting_niche.id)
    ]
    
    try:
        # Add all profiles
        for profile in golf_profiles + hunting_profiles:
            db.session.add(profile)
        
        db.session.commit()
        print("Successfully imported test profiles")
        
        # Print summary
        print("\nImported profiles:")
        print("\nGolf profiles:")
        for p in golf_profiles:
            print(f"- {p.username}")
        print("\nHunting profiles:")
        for p in hunting_profiles:
            print(f"- {p.username}")
            
    except Exception as e:
        print(f"Error importing profiles: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    import_test_profiles()