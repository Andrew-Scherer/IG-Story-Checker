import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

def verify_setup():
    """Verify database connection and table setup"""
    print("\n=== Verifying Database Setup ===")
    
    # Load environment variables
    load_dotenv()
    
    # Get database connection details
    db_user = os.getenv('POSTGRES_USER')
    db_pass = os.getenv('POSTGRES_PASSWORD')
    db_host = os.getenv('POSTGRES_HOST')
    db_port = os.getenv('POSTGRES_PORT')
    db_name = os.getenv('POSTGRES_DB')
    
    print("\nDatabase Configuration:")
    print(f"Host: {db_host}")
    print(f"Port: {db_port}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    
    # Create database URL
    db_url = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
    
    try:
        # Test connection
        print("\nTesting database connection...")
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("✓ Successfully connected to database")
            
            # Check tables
            print("\nChecking tables...")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print("\nExisting tables:")
            for table in sorted(tables):
                print(f"- {table}")
            
            # Check if required tables exist
            required_tables = {'profiles', 'niches', 'batches', 'proxies'}
            missing_tables = required_tables - set(tables)
            if missing_tables:
                print(f"\n❌ Missing required tables: {missing_tables}")
            else:
                print("\n✓ All required tables exist")
            
            # Check niche table content
            print("\nChecking niche table content...")
            result = conn.execute(text("SELECT COUNT(*) FROM niches"))
            niche_count = result.scalar()
            print(f"Number of niches: {niche_count}")
            
            # Check profile table content
            print("\nChecking profile table content...")
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN niche_id IS NOT NULL THEN 1 END) as with_niche,
                    COUNT(CASE WHEN niche_id IS NULL THEN 1 END) as without_niche
                FROM profiles
            """))
            row = result.fetchone()
            print(f"Total profiles: {row[0]}")
            print(f"Profiles with niche: {row[1]}")
            print(f"Profiles without niche: {row[2]}")
            
    except SQLAlchemyError as e:
        print(f"\n❌ Database error: {str(e)}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == '__main__':
    verify_setup()