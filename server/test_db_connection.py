import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables from .env file
load_dotenv()

# Construct the database URI
db_user = os.getenv('POSTGRES_USER', 'postgres')
db_pass = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
db_host = os.getenv('POSTGRES_HOST', 'localhost')
db_port = os.getenv('POSTGRES_PORT', '5432')
db_name = os.getenv('POSTGRES_TEST_DB', 'ig_story_checker_test')

db_uri = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'

print(f"Attempting to connect to: {db_uri}")

try:
    # Create engine and connect
    engine = create_engine(db_uri)
    with engine.connect() as connection:
        # Test the connection
        result = connection.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"Successfully connected to the database. PostgreSQL version: {version}")

        # Get list of tables
        try:
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            if tables:
                print("Tables in the database:")
                for table in tables:
                    print(f"- {table}")
            else:
                print("No tables found in the database.")
        except Exception as table_error:
            print(f"Error retrieving table list: {str(table_error)}")

except Exception as e:
    print(f"Error connecting to the database: {str(e)}")
finally:
    print("Database connection test completed.")
