"""
Add missing columns to batch_profiles and proxies tables
"""
from extensions import db
from sqlalchemy import text
from app import create_app

def add_missing_columns():
    app = create_app()
    with app.app_context():
        # Add columns to batch_profiles
        db.session.execute(text("""
            DO $$ 
            BEGIN
                BEGIN
                    ALTER TABLE batch_profiles 
                    ADD COLUMN proxy_id VARCHAR(36) REFERENCES proxies(id),
                    ADD COLUMN session_id INTEGER REFERENCES sessions(id);
                EXCEPTION
                    WHEN duplicate_column THEN 
                        RAISE NOTICE 'columns already exist in batch_profiles';
                END;

                BEGIN
                    ALTER TABLE proxies 
                    ADD COLUMN total_requests INTEGER NOT NULL DEFAULT 0,
                    ADD COLUMN failed_requests INTEGER NOT NULL DEFAULT 0,
                    ADD COLUMN requests_this_hour INTEGER NOT NULL DEFAULT 0,
                    ADD COLUMN error_count INTEGER NOT NULL DEFAULT 0;
                EXCEPTION
                    WHEN duplicate_column THEN 
                        RAISE NOTICE 'columns already exist in proxies';
                END;
            END $$;
        """))
        db.session.commit()
        print("Added missing columns successfully")

if __name__ == '__main__':
    add_missing_columns()
