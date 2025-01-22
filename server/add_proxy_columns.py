"""Add new columns to proxies table"""

import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

# Load environment variables
load_dotenv()

def add_columns():
    """Add rate_limited and last_used columns to proxies table"""
    
    # Connection parameters
    params = {
        'dbname': os.getenv('POSTGRES_DB'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT')
    }

    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        
        # Add rate_limited column if it doesn't exist
        print("Adding rate_limited column...")
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'proxies' AND column_name = 'rate_limited'
            ) THEN
                ALTER TABLE proxies ADD COLUMN rate_limited BOOLEAN DEFAULT FALSE;
            END IF;
        END
        $$;
        """)
        
        # Add last_used column if it doesn't exist
        print("Adding last_used column...")
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'proxies' AND column_name = 'last_used'
            ) THEN
                ALTER TABLE proxies ADD COLUMN last_used TIMESTAMP WITH TIME ZONE;
            END IF;
        END
        $$;
        """)
        
        conn.commit()
        print("Columns added successfully")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    add_columns()
