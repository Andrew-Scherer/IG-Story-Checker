"""
Flask extensions
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy with scoped session
db = SQLAlchemy(session_options={
    "scopefunc": None,  # Use default scope function
})
