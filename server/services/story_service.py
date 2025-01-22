"""
Story Service
Handles story-related operations
"""

from datetime import datetime, UTC, timedelta
from flask import current_app
from models import db, StoryResult

def cleanup_expired_stories():
    """Clean up expired story results"""
    try:
        expiration_time = datetime.now(UTC) - timedelta(hours=current_app.config['STORY_RESULT_RETENTION_HOURS'])
        expired_stories = StoryResult.query.filter(StoryResult.created_at < expiration_time).all()
        
        for story in expired_stories:
            db.session.delete(story)
        
        db.session.commit()
        current_app.logger.info(f"Cleaned up {len(expired_stories)} expired story results")
    except Exception as e:
        current_app.logger.error(f"Error cleaning up expired stories: {str(e)}")
        db.session.rollback()
