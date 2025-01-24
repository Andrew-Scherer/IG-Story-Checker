"""Add additional statistics columns to proxies table"""

import os
from sqlalchemy import create_engine, text

# Get database connection string from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def add_stats_columns():
    """Add statistics columns to proxies table"""
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        print("Adding statistics columns to proxies table...")
        
        # Add average response time column (in milliseconds)
        conn.execute(text("""
            ALTER TABLE proxies 
            ADD COLUMN IF NOT EXISTS avg_response_time INTEGER DEFAULT 0
        """))
        
        # Add last error message column
        conn.execute(text("""
            ALTER TABLE proxies 
            ADD COLUMN IF NOT EXISTS last_error TEXT
        """))
        
        # Add last success timestamp column
        conn.execute(text("""
            ALTER TABLE proxies 
            ADD COLUMN IF NOT EXISTS last_success TIMESTAMP WITH TIME ZONE
        """))
        
        conn.commit()
        print("Statistics columns added successfully")

if __name__ == '__main__':
    add_stats_columns()
