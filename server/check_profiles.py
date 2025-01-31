import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection details
db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
db_name = os.getenv('POSTGRES_DB')

# Create database connection
db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(db_url)

def check_profiles():
    """Check profiles in the database"""
    with engine.connect() as conn:
        # Get total count
        result = conn.execute(text('SELECT COUNT(*) FROM profiles'))
        total_count = result.scalar()
        print(f"\nTotal profiles in database: {total_count}")

        # Get all profiles with niche names
        result = conn.execute(text('''
            SELECT p.username, p.status, p.niche_id, n.name as niche_name
            FROM profiles p
            LEFT JOIN niches n ON p.niche_id = n.id
            ORDER BY username
        '''))
        print("\nAll profiles:")
        for row in result:
            print(f"Username: {row.username:<30} Status: {row.status:<10} Niche: {row.niche_name or 'None'} (ID: {row.niche_id or 'None'})")

        # Check for similar usernames
        print("\nChecking for similar usernames:")
        query = text("""
            SELECT p1.username as username1, p2.username as username2
            FROM profiles p1
            JOIN profiles p2 ON LOWER(p1.username) = LOWER(p2.username)
                OR REPLACE(LOWER(p1.username), '.', '_') = REPLACE(LOWER(p2.username), '.', '_')
            WHERE p1.id != p2.id
            ORDER BY p1.username
        """)
        result = conn.execute(query)
        similar_pairs = result.fetchall()
        if similar_pairs:
            print("\nFound similar username pairs:")
            for row in similar_pairs:
                print(f"{row.username1} <-> {row.username2}")
        else:
            print("No similar usernames found")

if __name__ == '__main__':
    check_profiles()