"""Check foreign key references to sessions table"""

import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'overwatch23562')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'ig_story_checker_dev')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def check_references():
    """Check all foreign key references to sessions table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("\n=== Checking References to Sessions Table ===")
        result = conn.execute(text("""
            SELECT
                tc.table_schema, 
                tc.table_name, 
                kcu.column_name,
                tc.constraint_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'sessions';
        """))
        
        references = []
        for row in result:
            references.append({
                'table': f"{row[0]}.{row[1]}",
                'column': row[2],
                'constraint': row[3],
                'references': f"{row[4]}.{row[5]}.{row[6]}"
            })
        
        if references:
            print("\nFound references:")
            for ref in references:
                print(f"- {ref['table']}.{ref['column']} -> {ref['references']} ({ref['constraint']})")
        else:
            print("\nNo foreign key references found to sessions table")
            
        print("\n=== Checking Sessions Table Structure ===")
        result = conn.execute(text("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'sessions'
            ORDER BY ordinal_position;
        """))
        
        print("\nColumns:")
        for row in result:
            print(f"- {row[0]}: {row[1]}" + 
                  (f" DEFAULT {row[2]}" if row[2] else "") +
                  (f" NULL" if row[3] == 'YES' else " NOT NULL"))

if __name__ == '__main__':
    check_references()