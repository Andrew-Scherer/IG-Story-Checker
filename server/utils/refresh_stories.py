"""
Simple script to update active_story status for profiles with stories older than 24 hours
"""

from datetime import datetime, timedelta, UTC
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
db_params = {
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'database': os.getenv('POSTGRES_DB')
}

def refresh_stories():
    """Update active_story status for profiles with old stories"""
    
    # Create database connection
    db_url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Calculate cutoff time (24 hours ago)
            cutoff_time = datetime.now(UTC) - timedelta(hours=24)
            
            # Update profiles where last_story_detected is older than 24 hours
            result = conn.execute(
                text("""
                UPDATE profiles 
                SET active_story = false 
                WHERE active_story = true 
                AND last_story_detected < :cutoff_time
                """),
                {"cutoff_time": cutoff_time}
            )
            
            # Commit the transaction
            conn.commit()
            
            # Print results
            print(f"Updated {result.rowcount} profiles")
            
    except Exception as e:
        print(f"Error refreshing stories: {str(e)}")
        raise

if __name__ == '__main__':
    refresh_stories()
