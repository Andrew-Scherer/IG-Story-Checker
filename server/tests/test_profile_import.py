import os
import sys
from pathlib import Path
from flask import Flask
from sqlalchemy import select, func
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the server directory to Python path
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

from extensions import db
from models.profile import Profile
from api.profile import profile_bp

def create_test_app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    
    # Get database connection details from environment or use defaults
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/ig_story_checker_test'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.register_blueprint(profile_bp, url_prefix='/api/profiles')
    db.init_app(app)
    return app

def analyze_import_results(created_profiles, errors):
    """Analyze the results of profile import"""
    logger.info("\n=== Import Analysis ===")
    logger.info(f"Total profiles attempted: {len(created_profiles) + len(errors)}")
    logger.info(f"Successfully created: {len(created_profiles)}")
    logger.info(f"Errors: {len(errors)}")
    
    # Analyze error types
    error_types = {}
    for error in errors:
        error_type = error['error']
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    logger.info("\nError breakdown:")
    for error_type, count in error_types.items():
        logger.info(f"- {error_type}: {count}")
    
    # Analyze duplicate patterns
    if 'Profile already exists' in error_types:
        logger.info("\nAnalyzing duplicate patterns:")
        duplicates = [error['line'] for error in errors if error['error'] == 'Profile already exists']
        logger.info(f"Total duplicates found: {len(duplicates)}")
        logger.info("Sample duplicates:")
        for dup in duplicates[:5]:  # Show first 5 duplicates
            logger.info(f"- {dup}")

def test_profile_import():
    """Test profile import with test dataset"""
    app = create_test_app()
    
    with app.app_context():
        try:
            # Clear existing profiles
            db.session.query(Profile).delete()
            db.session.commit()
            
            logger.info("\n=== Starting Profile Import Test ===")
            
            # Read test profiles
            test_file_path = Path(__file__).parent / 'test_data' / 'test_profiles.txt'
            with open(test_file_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            logger.info(f"Loaded {len(lines)} test profiles")
            
            # First pass: Import original profiles
            logger.info("\nFirst pass - importing original profiles...")
            created_first = []
            errors_first = []
            
            for line in lines[:3]:  # First 3 profiles are our originals
                try:
                    # Extract username from URL if needed
                    if 'instagram.com' in line:
                        username = line.split('/')[-1]
                    else:
                        username = line
                        
                    logger.debug(f"Attempting to create profile: {username}")
                    profile = Profile(
                        username=username,
                        url=f"https://instagram.com/{username}",
                        status='active'
                    )
                    db.session.add(profile)
                    db.session.flush()
                    created_first.append(profile.to_dict())
                    logger.debug(f"Successfully created profile: {username}")
                except Exception as e:
                    logger.error(f"Error creating profile {line}: {str(e)}")
                    errors_first.append({'line': line, 'error': str(e)})
            
            if created_first:
                db.session.commit()
                logger.info(f"Committed {len(created_first)} profiles")
            
            # Second pass: Try to import all profiles
            logger.info("\nSecond pass - importing all profiles...")
            created_second = []
            errors_second = []
            
            for line in lines:
                try:
                    # Extract username from URL if needed
                    if 'instagram.com' in line:
                        username = line.split('/')[-1]
                    else:
                        username = line
                    
                    logger.debug(f"Checking for existing profile: {username}")
                    # Check for existing profile
                    existing = db.session.execute(
                        select(Profile).where(Profile.username == username)
                    ).scalar()
                    
                    if existing:
                        logger.debug(f"Found existing profile: {username}")
                        errors_second.append({
                            'line': line,
                            'error': 'Profile already exists'
                        })
                        continue
                    
                    logger.debug(f"Creating new profile: {username}")
                    profile = Profile(
                        username=username,
                        url=f"https://instagram.com/{username}",
                        status='active'
                    )
                    db.session.add(profile)
                    db.session.flush()
                    created_second.append(profile.to_dict())
                    logger.debug(f"Successfully created profile: {username}")
                    
                except Exception as e:
                    logger.error(f"Error processing profile {line}: {str(e)}")
                    errors_second.append({'line': line, 'error': str(e)})
            
            if created_second:
                db.session.commit()
                logger.info(f"Committed {len(created_second)} profiles")
            
            # Analyze results
            logger.info("\n=== First Pass Analysis ===")
            analyze_import_results(created_first, errors_first)
            
            logger.info("\n=== Second Pass Analysis ===")
            analyze_import_results(created_second, errors_second)
            
            # Query final database state
            total_profiles = db.session.execute(select(func.count()).select_from(Profile)).scalar()
            logger.info(f"\nFinal database state: {total_profiles} total profiles")
            
            # Analyze username patterns in duplicates
            if errors_second:
                duplicate_usernames = [
                    error['line'] for error in errors_second 
                    if error['error'] == 'Profile already exists'
                ]
                if duplicate_usernames:
                    logger.info("\n=== Duplicate Username Analysis ===")
                    logger.info("Sample of duplicate usernames and their variations:")
                    for username in duplicate_usernames[:5]:
                        similar_profiles = db.session.execute(
                            select(Profile.username).where(Profile.username.ilike(f"%{username}%"))
                        ).scalars().all()
                        logger.info(f"\nOriginal: {username}")
                        logger.info(f"Similar profiles in DB: {similar_profiles}")
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}", exc_info=True)
            db.session.rollback()
            raise

if __name__ == '__main__':
    test_profile_import()