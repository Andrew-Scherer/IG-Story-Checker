"""
Fix batch state and database schema issues
"""

import os
from sqlalchemy import create_engine, text
from flask import current_app
from app import create_app
from extensions import db

# Get database URL from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def fix_database_schema():
    """Fix database schema issues"""
    engine = create_engine(DATABASE_URL)
    
    print("Fixing database schema...")
    with engine.connect() as conn:
        # First fix sessions table
        print("\n1. Fixing sessions table...")
        conn.execute(text("""
            -- Drop existing foreign keys that reference sessions.id
            DO $$ 
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'proxy_error_logs_session_id_fkey'
                ) THEN
                    ALTER TABLE proxy_error_logs DROP CONSTRAINT proxy_error_logs_session_id_fkey;
                END IF;
            END $$;
            
            -- Drop the sequence dependency
            ALTER TABLE sessions ALTER COLUMN id DROP DEFAULT;
            DROP SEQUENCE IF EXISTS sessions_id_seq CASCADE;
            
            -- Create temporary column for conversion
            ALTER TABLE sessions ADD COLUMN new_id varchar(36);
            UPDATE sessions SET new_id = gen_random_uuid()::text;
            
            -- Drop old column and rename new
            ALTER TABLE sessions DROP COLUMN id;
            ALTER TABLE sessions RENAME COLUMN new_id TO id;
            
            -- Make id the primary key
            ALTER TABLE sessions ADD PRIMARY KEY (id);
            ALTER TABLE sessions ALTER COLUMN id SET DEFAULT gen_random_uuid()::text;
        """))
        print("Sessions table fixed")
        
        # Now fix proxy_error_logs table
        print("\n2. Fixing proxy_error_logs table...")
        conn.execute(text("""
            -- Add missing columns if they don't exist
            DO $$ 
            BEGIN
                -- Add session_id
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'proxy_error_logs' 
                    AND column_name = 'session_id'
                ) THEN
                    ALTER TABLE proxy_error_logs 
                    ADD COLUMN session_id varchar(36) REFERENCES sessions(id) ON DELETE SET NULL;
                END IF;
                
                -- Add state_change
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'proxy_error_logs' 
                    AND column_name = 'state_change'
                ) THEN
                    ALTER TABLE proxy_error_logs 
                    ADD COLUMN state_change boolean DEFAULT false;
                END IF;
                
                -- Add transition_reason
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'proxy_error_logs' 
                    AND column_name = 'transition_reason'
                ) THEN
                    ALTER TABLE proxy_error_logs 
                    ADD COLUMN transition_reason text;
                END IF;
                
                -- Add recovery_time
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'proxy_error_logs' 
                    AND column_name = 'recovery_time'
                ) THEN
                    ALTER TABLE proxy_error_logs 
                    ADD COLUMN recovery_time timestamp with time zone;
                END IF;
            END $$;
        """))
        print("Proxy error logs table fixed")
        
        conn.commit()
        print("\nSchema fixes committed successfully")

def reset_batch_state():
    """Reset stuck batch state and reorder queue"""
    app = create_app()
    with app.app_context():
        print("\n3. Resetting batch states...")
        
        # Reset any batch in position 0 to queued
        result = db.session.execute(text("""
            UPDATE batches 
            SET status = 'queued',
                queue_position = NULL 
            WHERE queue_position = 0
            RETURNING id;
        """))
        reset_ids = [row[0] for row in result]
        
        if reset_ids:
            print(f"Reset batches: {reset_ids}")
        else:
            print("No batches in position 0")
            
        # Reorder remaining queue
        db.session.execute(text("""
            WITH numbered AS (
                SELECT id, ROW_NUMBER() OVER (ORDER BY queue_position) AS new_position
                FROM batches 
                WHERE queue_position > 0
            )
            UPDATE batches 
            SET queue_position = numbered.new_position
            FROM numbered
            WHERE batches.id = numbered.id;
        """))
        
        db.session.commit()
        print("Queue reordering complete")

if __name__ == '__main__':
    print("=== Starting Fix ===")
    fix_database_schema()
    reset_batch_state()
    print("=== Fix Complete ===")