from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from models import SystemSettings, Niche
from sqlalchemy import select
import uuid

def seed_database():
    app = create_app()
    with app.app_context():
        # Create default system settings if they don't exist
        stmt = select(SystemSettings).where(SystemSettings.id == 1)
        settings = db.session.execute(stmt).scalar_one_or_none()
        
        if not settings:
            settings = SystemSettings()
            db.session.add(settings)
            try:
                db.session.commit()
                print("Created default system settings")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating system settings: {e}")
        else:
            print("Default system settings already exist")
            
        # Create default niche if it doesn't exist
        stmt = select(Niche).where(Niche.id == '1')
        niche = db.session.execute(stmt).scalar_one_or_none()
        
        if not niche:
            niche = Niche(
                id='1',  # Use string '1' to match UUID format
                name='Default Niche',
                daily_story_target=10
            )
            db.session.add(niche)
            try:
                db.session.commit()
                print("Created default niche")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating default niche: {e}")
        else:
            print("Default niche already exists")

if __name__ == '__main__':
    seed_database()
