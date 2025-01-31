import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the server directory to Python path
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

from extensions import db
from models.profile import Profile
from models.niche import Niche

def setup_test_database():
    """Create and set up test database"""
    conn = None
    try:
        # Get test database connection details from environment
        db_user = os.getenv('TEST_DB_USER')
        db_password = os.getenv('TEST_DB_PASSWORD')
        db_host = os.getenv('TEST_DB_HOST')
        db_port = os.getenv('TEST_DB_PORT')
        db_name = os.getenv('TEST_DB_NAME')

        print(f"Connecting to PostgreSQL server at {db_host}:{db_port}...")
        
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create test database
        cur = conn.cursor()
        print("Creating test database...")
        
        # Drop database if it exists
        cur.execute("DROP DATABASE IF EXISTS ig_story_checker_test")
        
        # Create new database
        cur.execute("CREATE DATABASE ig_story_checker_test")
        cur.close()
        conn.close()
        
        print("Test database created successfully")
        
        # Connect to the new database and create tables
        from app import create_app
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/ig_story_checker_test'
        )
        
        with app.app_context():
            print("Creating tables...")
            db.create_all()
            
            # Create a test niche
            test_niche = Niche(name='Test Niche')
            db.session.add(test_niche)
            db.session.commit()
            
            print("Test database setup complete!")
            return True
            
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error setting up test database: {e}")
        return False
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    success = setup_test_database()
    if not success:
        sys.exit(1)