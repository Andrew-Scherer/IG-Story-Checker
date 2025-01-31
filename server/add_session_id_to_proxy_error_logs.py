"""Add session_id column to proxy_error_logs table"""

from sqlalchemy import create_engine, MetaData, Table, Column, String, ForeignKey, text
import os

# Get database URL from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def upgrade():
    """Add session_id column"""
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    # Get proxy_error_logs table
    proxy_error_logs = Table('proxy_error_logs', metadata, autoload_with=engine)
    
    # Add session_id column if it doesn't exist
    if 'session_id' not in proxy_error_logs.columns:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE proxy_error_logs 
                ADD COLUMN session_id VARCHAR(36) REFERENCES sessions(id)
            """))
            conn.commit()
            print("Added session_id column to proxy_error_logs table")
    else:
        print("session_id column already exists")

if __name__ == '__main__':
    upgrade()