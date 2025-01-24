"""Add status column to proxies table"""

import os
from sqlalchemy import create_engine, text

# Get database connection string from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def add_status_column():
    """Add status column to proxies table"""
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        print("Adding status column to proxies table...")
        
        # Add status column with default value 'active'
        conn.execute(text("""
            ALTER TABLE proxies 
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'
        """))
        
        conn.commit()
        print("Status column added successfully")

if __name__ == '__main__':
    add_status_column()
