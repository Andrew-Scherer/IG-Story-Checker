"""Add queue_position column to batches table"""

import os
from dotenv import load_dotenv
import psycopg2
from flask import current_app

# Load environment variables
load_dotenv()

def add_queue_position():
    # Connection parameters
    params = {
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
        'database': os.getenv('POSTGRES_DB')
    }

    try:
        # Connect to database
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='batches' AND column_name='queue_position';
        """)
        
        if not cur.fetchone():
            # Add queue_position column
            cur.execute('ALTER TABLE batches ADD COLUMN queue_position INTEGER;')
            print('Added queue_position column to batches table')
        else:
            print('queue_position column already exists')

        cur.close()
        conn.close()

    except Exception as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    add_queue_position()
