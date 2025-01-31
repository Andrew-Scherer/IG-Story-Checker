"""Add state_change, transition_reason, and recovery_time columns to proxy_error_logs table."""

import os
from sqlalchemy import create_engine, text

# Get database connection string from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def add_state_columns_to_proxy_error_logs():
    """Add new columns to the proxy_error_logs table."""
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        print("Adding new columns to proxy_error_logs table...")

        conn.execute(text('''
            ALTER TABLE proxy_error_logs
            ADD COLUMN IF NOT EXISTS state_change BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS transition_reason TEXT,
            ADD COLUMN IF NOT EXISTS recovery_time TIMESTAMP WITH TIME ZONE;
        '''))

        conn.commit()
        print("Columns added successfully to proxy_error_logs table.")

if __name__ == '__main__':
    add_state_columns_to_proxy_error_logs()