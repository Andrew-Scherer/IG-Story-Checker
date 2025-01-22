from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        result = db.session.execute(text('SELECT 1')).scalar()
        print('Database connection successful' if result == 1 else 'Database connection failed')
        
        # Also verify we can query a table
        niches_count = db.session.execute(text('SELECT COUNT(*) FROM niches')).scalar()
        print(f'Number of niches in database: {niches_count}')
    except Exception as e:
        print(f'Database connection error: {e}')
