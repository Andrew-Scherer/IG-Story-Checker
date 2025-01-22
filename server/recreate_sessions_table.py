"""
Drop and recreate sessions table
"""
from app import create_app
from extensions import db
from sqlalchemy import text
from models.session import Session

def recreate_sessions_table():
    """Drop and recreate sessions table"""
    app = create_app()
    with app.app_context():
        # Drop table
        db.session.execute(text('DROP TABLE IF EXISTS sessions CASCADE'))
        db.session.commit()
        
        # Create table
        Session.__table__.create(db.engine)
        print("Recreated sessions table successfully")

if __name__ == '__main__':
    recreate_sessions_table()
