"""
Database initialization script
Creates databases and runs initial migrations
"""
import os
import sys
import subprocess
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

def init_db():
    """Initialize development and test databases"""
    databases = [
        'postgresql://localhost/ig_story_checker',
        'postgresql://localhost/ig_story_checker_test'
    ]
    
    for db_url in databases:
        engine = create_engine(db_url)
        if not database_exists(engine.url):
            create_database(engine.url)
            print(f"Created database: {engine.url}")
        else:
            print(f"Database already exists: {engine.url}")

    # Initialize migrations
    subprocess.run(['flask', 'db', 'init'], check=True)
    subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration'], check=True)
    subprocess.run(['flask', 'db', 'upgrade'], check=True)

if __name__ == '__main__':
    init_db()
