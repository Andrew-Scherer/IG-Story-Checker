"""
Drop and recreate proxies table
"""
from app import create_app
from extensions import db
from sqlalchemy import text
from models.proxy import Proxy

def recreate_proxies_table():
    """Drop and recreate proxies table"""
    app = create_app()
    with app.app_context():
        # Drop table
        db.session.execute(text('DROP TABLE IF EXISTS proxies CASCADE'))
        db.session.commit()
        
        # Create table
        Proxy.__table__.create(db.engine)
        print("Recreated proxies table successfully")

if __name__ == '__main__':
    recreate_proxies_table()
