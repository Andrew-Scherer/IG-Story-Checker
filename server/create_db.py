import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def create_database():
    # Connection parameters for the default postgres database
    params = {
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
        'database': 'postgres'  # Connect to default database first
    }

    try:
        # Connect to default database
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()

        # Create test database
        test_db = os.getenv('POSTGRES_TEST_DB')
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{test_db}'")
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE {test_db}')
            print(f'Database {test_db} created successfully')
        else:
            print(f'Database {test_db} already exists')

        cur.close()
        conn.close()

    except Exception as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    create_database()
