"""Check database schema"""

import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def check_schema():
    """Check table schemas"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # First check if tables exist
            print("\n=== Checking Tables ===")
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
            print("Executing query:", tables_query)
            result = conn.execute(text(tables_query))
            tables = [row[0] for row in result]
            print("Found tables:", tables)
            
            if 'sessions' not in tables:
                print("\nWARNING: sessions table does not exist!")
            else:
                # Check sessions table
                print("\n=== Sessions Table ===")
                print("Columns:")
                sessions_query = """
                    SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'sessions'
                    ORDER BY ordinal_position;
                """
                print("Executing query:", sessions_query)
                result = conn.execute(text(sessions_query))
                for row in result:
                    print(f"{row[0]}: {row[1]}" + (f"({row[2]})" if row[2] else "") + 
                          f" {'NULL' if row[3] == 'YES' else 'NOT NULL'}" +
                          (f" DEFAULT {row[4]}" if row[4] else ""))

            if 'proxy_error_logs' not in tables:
                print("\nWARNING: proxy_error_logs table does not exist!")
            else:
                # Check proxy_error_logs table
                print("\n=== Proxy Error Logs Table ===")
                print("Columns:")
                logs_query = """
                    SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'proxy_error_logs'
                    ORDER BY ordinal_position;
                """
                print("Executing query:", logs_query)
                result = conn.execute(text(logs_query))
                for row in result:
                    print(f"{row[0]}: {row[1]}" + (f"({row[2]})" if row[2] else "") + 
                          f" {'NULL' if row[3] == 'YES' else 'NOT NULL'}" +
                          (f" DEFAULT {row[4]}" if row[4] else ""))
                
                print("\nForeign Keys:")
                fk_query = """
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'proxy_error_logs';
                """
                print("Executing query:", fk_query)
                result = conn.execute(text(fk_query))
                for row in result:
                    print(f"- {row[1]} -> {row[2]}.{row[3]} ({row[0]})")
    
    except Exception as e:
        print(f"Error checking schema: {str(e)}")

if __name__ == '__main__':
    print("=== Checking Database Schema ===")
    check_schema()
    print("\n=== Schema Check Complete ===")