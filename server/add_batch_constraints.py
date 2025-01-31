"""
Add batch state and position constraints
"""

from app import create_app
from models import db
from sqlalchemy import text

def add_batch_constraints():
    """Add constraints to batches table"""
    print("Adding batch constraints...")
    
    # Create unique index for position (except null)
    db.session.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_position
        ON batches (position)
        WHERE position IS NOT NULL
    """))
    
    # Drop existing constraints if they exist
    db.session.execute(text("""
        DO $$ 
        BEGIN
            BEGIN
                ALTER TABLE batches DROP CONSTRAINT valid_states;
            EXCEPTION
                WHEN undefined_object THEN NULL;
            END;
            
            BEGIN
                ALTER TABLE batches DROP CONSTRAINT position_rules;
            EXCEPTION
                WHEN undefined_object THEN NULL;
            END;
        END $$;
    """))
    
    # Add valid states check
    db.session.execute(text("""
        ALTER TABLE batches
        ADD CONSTRAINT valid_states
        CHECK (status IN ('queued', 'running', 'paused', 'done', 'error'))
    """))
    
    # Add position rules check
    db.session.execute(text("""
        ALTER TABLE batches
        ADD CONSTRAINT position_rules
        CHECK (
            (status IN ('paused', 'done', 'error') AND position IS NULL) OR
            (status = 'running' AND position = 0) OR
            (status = 'queued' AND position > 0)
        )
    """))
    
    db.session.commit()
    print("Batch constraints added successfully")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        add_batch_constraints()