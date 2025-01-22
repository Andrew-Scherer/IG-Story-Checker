"""
Batch utilities
"""

from flask import current_app
from models import db

def notify_batch_update(batch):
    """Notify batch update - called when:
    1. A batch is created
    2. A batch is completed
    3. A batch status is manually checked
    """
    # Just update the batch stats - client will get updates through API calls
    batch.update_stats()
    db.session.commit()
