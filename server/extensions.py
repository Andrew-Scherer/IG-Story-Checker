"""
Flask Extensions
Initializes Flask extensions for use across the application
"""

from flask_sqlalchemy import SQLAlchemy

# Create Flask-SQLAlchemy instance
db = SQLAlchemy()
