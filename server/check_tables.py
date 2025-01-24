import os
from sqlalchemy import create_engine, inspect

# Get database connection string from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def list_tables():
    """List all tables in the database."""
    engine = create_engine(DB_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables in the database:")
    for table in tables:
        print(f" - {table}")

if __name__ == '__main__':
    list_tables()
