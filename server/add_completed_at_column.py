import os
import psycopg2

def add_completed_at_column():
    """Add 'completed_at' column to 'batches' table if it doesn't exist."""
    # Database connection parameters
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = 'overwatch23562'  # Set the password directly
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

    # Connect to the database
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )

    try:
        with conn:
            with conn.cursor() as cur:
                # Check if the column already exists
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='batches' AND column_name='completed_at';
                """)
                result = cur.fetchone()
                if result:
                    print("Column 'completed_at' already exists in 'batches' table.")
                else:
                    # Add the 'completed_at' column
                    cur.execute("""
                        ALTER TABLE batches 
                        ADD COLUMN completed_at TIMESTAMP WITH TIME ZONE;
                    """)
                    print("Column 'completed_at' added to 'batches' table successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_completed_at_column()
