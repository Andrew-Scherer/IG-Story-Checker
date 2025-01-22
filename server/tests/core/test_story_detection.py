"""
Test story detection functionality
"""
import pytest
from flask import Flask
from extensions import db
from models import Proxy, Session
from core.story_checker import StoryChecker
from core.proxy_session import ProxySession

@pytest.mark.parametrize("username,expected", [
    # Profiles to verify
    ("annabellessmile", True),
    ("_tattooed_barbie_", True)
])
@pytest.mark.asyncio
async def test_story_detection(username, expected):
    """Test if story detection can identify active stories"""
    # Create Flask app context for database access
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:overwatch23562@localhost:5432/ig_story_checker_dev'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Get first available proxy and session
        proxy_session = db.session.query(Proxy, Session).join(Session).first()
        if not proxy_session:
            pytest.skip("No proxy/session pairs available for testing")
            
        proxy, session = proxy_session
        proxy_session = ProxySession(proxy, session)
        
        # Create story checker with proxy session
        checker = StoryChecker(proxy_session)
        
        try:
            # Check story
            result = await checker.check_story(username)
            assert result == expected, f"Story detection failed for {username}"
        finally:
            # Clean up
            await checker.cleanup()
