"""Add proxy_error_logs table to the database."""

import os
from sqlalchemy import create_engine, text

# Get database connection string from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def add_proxy_error_logs_table():
    """Create the proxy_error_logs table."""
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        print("Creating proxy_error_logs table...")

        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS proxy_error_logs (
                id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
                proxy_id VARCHAR(36) NOT NULL REFERENCES proxies (id) ON DELETE CASCADE,
                error_message TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        '''))

        conn.commit()
        print("proxy_error_logs table created successfully.")

if __name__ == '__main__':
    add_proxy_error_logs_table()
