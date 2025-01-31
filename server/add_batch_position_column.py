"""
Add position column to batches table
"""

from app import create_app
from models import db
from sqlalchemy import text

def add_batch_position_column():
    """Add position column to batches table"""
    print("Adding position column to batches table...")
    
    # Add position column
    db.session.execute(text("""
        ALTER TABLE batches
        ADD COLUMN IF NOT EXISTS position INTEGER
    """))
    
    # Initialize existing batches
    db.session.execute(text("""
        UPDATE batches
        SET position = NULL
        WHERE position IS NULL
    """))
    
    db.session.commit()
    print("Position column added successfully")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        add_batch_position_column()