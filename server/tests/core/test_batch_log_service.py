"""
Test batch log service functionality
"""

import pytest
import logging
import sys
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import joinedload
from models import db
from models.batch import Batch
from models.batch_log import BatchLog
from models.profile import Profile
from models.proxy import Proxy
from models.niche import Niche
from services.batch_log_service import BatchLogService
import uuid
from tests.core.test_batch_processor import engine, tables, db_session, app

# Set up logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)

@pytest.fixture
def test_batch(db_session):
    """Create a test batch"""
    niche = Niche(name="Test Niche")
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username=f"test_user_{uuid.uuid4().hex[:8]}", niche=niche)
    db_session.add(profile)
    db_session.commit()

    batch = Batch(niche_id=niche.id, profile_ids=[profile.id])
    batch.status = 'running'
    db_session.add(batch)
    db_session.commit()
    return batch

@pytest.fixture
def test_profile(db_session, test_batch):
    """Create a test profile"""
    profile = test_batch.profiles[0]
    return profile

@pytest.fixture
def test_proxy(db_session):
    """Create a test proxy"""
    proxy = Proxy(
        ip="127.0.0.1",
        port=8080,
        username="testuser",
        password="testpass",
        is_active=True
    )
    db_session.add(proxy)
    db_session.commit()
    return proxy

@pytest.mark.real_db
def test_create_log_basic(app, db_session, test_batch):
    """Test basic log creation"""
    with app.app_context():
        # Create log
        log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="TEST_EVENT",
            message="Test log message"
        )
        db_session.commit()

        # Verify log was created
        saved_log = db_session.query(BatchLog).filter_by(id=log.id).first()
        assert saved_log is not None
        assert saved_log.batch_id == test_batch.id
        assert saved_log.event_type == "TEST_EVENT"
        assert saved_log.message == "Test log message"
        assert saved_log.timestamp is not None

@pytest.mark.real_db
def test_create_log_with_profile(app, db_session, test_batch, test_profile):
    """Test log creation with profile reference"""
    with app.app_context():
        # Ensure BatchProfile exists
        db_session.add(test_profile)
        db_session.commit()

        # Fetch the Profile via BatchProfile
        persisted_profile = db_session.query(Profile).filter_by(id=test_profile.profile_id).first()
        assert persisted_profile is not None  # Ensure profile exists

        # Create log referencing the profile
        log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="PROFILE_EVENT",
            message=f"Checked profile {persisted_profile.username}",
            profile_id=persisted_profile.id
        )
        db_session.commit()

        # Verify log and relationship
        saved_log = (
            db_session.query(BatchLog)
            .options(joinedload(BatchLog.profile))
            .filter_by(id=log.id)
            .first()
        )
        assert saved_log is not None
        assert saved_log.profile_id == persisted_profile.id
        assert saved_log.profile.username == persisted_profile.username

@pytest.mark.real_db
def test_create_log_with_proxy(app, db_session, test_batch, test_proxy):
    """Test log creation with proxy reference"""
    with app.app_context():
        # Create log with proxy
        log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="PROXY_EVENT",
            message="Test proxy log",
            proxy_id=test_proxy.id
        )
        db_session.commit()

        # Verify log and relationship
        saved_log = db_session.query(BatchLog).filter_by(id=log.id).first()
        assert saved_log.proxy_id == test_proxy.id
        assert saved_log.proxy == test_proxy

@pytest.mark.real_db
def test_create_log_error_handling(app, db_session):
    """Test error handling in log creation"""
    with app.app_context():
        # Test with invalid batch ID
        with pytest.raises(Exception):
            BatchLogService.create_log(
                batch_id="invalid_id",
                event_type="TEST_EVENT",
                message="Test message"
            )

@pytest.mark.real_db
def test_get_logs_basic(app, db_session, test_batch):
    """Test basic log retrieval"""
    with app.app_context():
        # Create multiple logs
        for i in range(5):
            BatchLogService.create_log(
                batch_id=test_batch.id,
                event_type=f"EVENT_{i}",
                message=f"Test message {i}"
            )
        db_session.commit()

        # Retrieve logs
        logs, total = BatchLogService.get_logs(test_batch.id)
        assert total == 5
        assert len(logs) == 5
        # Verify descending order by timestamp
        for i in range(len(logs) - 1):
            assert logs[i].timestamp >= logs[i + 1].timestamp

@pytest.mark.real_db
def test_get_logs_with_time_filter(app, db_session, test_batch):
    """Test log retrieval with time filtering"""
    with app.app_context():
        now = datetime.now(UTC)

        # Create old log (2 hours ago)
        old_log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="OLD_EVENT",
            message="Old message"
        )
        # Set timestamp after creation
        old_log.timestamp = now - timedelta(hours=2)
        db_session.commit()

        # Create recent log (now)
        recent_log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="RECENT_EVENT",
            message="Recent message"
        )
        # Set timestamp after creation
        recent_log.timestamp = now
        db_session.commit()

        # Test time filtering
        logs, total = BatchLogService.get_logs(
            test_batch.id,
            start_time=old_log.timestamp + timedelta(seconds=1)  # Get logs after old log
        )
        assert total == 1
        assert logs[0].event_type == "RECENT_EVENT"

@pytest.mark.real_db
def test_get_logs_pagination(app, db_session, test_batch):
    """Test log retrieval pagination"""
    with app.app_context():
        # Create 15 logs
        for i in range(15):
            BatchLogService.create_log(
                batch_id=test_batch.id,
                event_type=f"EVENT_{i}",
                message=f"Test message {i}"
            )
        db_session.commit()

        # Test first page
        logs, total = BatchLogService.get_logs(test_batch.id, limit=10, offset=0)
        assert total == 15
        assert len(logs) == 10

        # Test second page
        logs, total = BatchLogService.get_logs(test_batch.id, limit=10, offset=10)
        assert total == 15
        assert len(logs) == 5

@pytest.mark.real_db
def test_log_persistence(app, db_session, test_batch):
    """Test log persistence and relationship loading"""
    with app.app_context():
        # Create and commit log
        log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="TEST_EVENT",
            message="Test message"
        )
        db_session.commit()
        log_id = log.id

        # Reload log before expunging
        reloaded_log = (
            db_session.query(BatchLog)
            .options(joinedload(BatchLog.batch))  # Preload batch relationship
            .filter_by(id=log_id)
            .first()
        )

        # Store values before expunging
        batch_id = reloaded_log.batch_id
        event_type = reloaded_log.event_type
        message = reloaded_log.message

        # Now it's safe to expunge session
        db_session.expunge_all()

        assert reloaded_log is not None
        assert batch_id == test_batch.id  # Compare stored ID
        assert event_type == "TEST_EVENT"
        assert message == "Test message"

@pytest.mark.real_db
def test_batch_deletion_cascade(app, db_session, test_batch):
    """Test log deletion when batch is deleted"""
    with app.app_context():
        # Create log
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="TEST_EVENT",
            message="Test message"
        )
        db_session.commit()

        # Count logs
        initial_count = db_session.query(BatchLog).filter_by(batch_id=test_batch.id).count()
        assert initial_count > 0

        # Delete batch
        db_session.delete(test_batch)
        db_session.commit()

        # Verify logs were deleted
        final_count = db_session.query(BatchLog).filter_by(batch_id=test_batch.id).count()
        assert final_count == 0

@pytest.mark.real_db
def test_create_log_profile_checker(app, db_session, test_batch, test_profile):
    """Test logging of profile checking events"""
    with app.app_context():
        # Ensure profile exists in DB
        db_session.add(test_profile)
        db_session.commit()

        # Get the actual Profile from BatchProfile
        persisted_profile = db_session.query(Profile).filter_by(id=test_profile.profile_id).first()
        assert persisted_profile is not None  # Ensure profile exists

        # Store profile info to avoid detached instance issues
        profile_id = persisted_profile.id
        username = persisted_profile.username

        # Test successful story check with story found
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="PROFILE_CHECK",
            message=f"Successfully checked {username} (has_story=True)",
            profile_id=profile_id
        )
        db_session.commit()

        # Test successful story check with no story
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="PROFILE_CHECK",
            message=f"Successfully checked {username} (has_story=False)",
            profile_id=profile_id
        )
        db_session.commit()

        # Test story check failure
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="PROFILE_ERROR",
            message=f"Failed to check {username}: Rate limited",
            profile_id=profile_id
        )
        db_session.commit()

        # Verify logs were created
        logs, total = BatchLogService.get_logs(test_batch.id)
        assert total == 3
        
        # Get logs in chronological order with relationships loaded
        logs = (
            db_session.query(BatchLog)
            .options(joinedload(BatchLog.profile))
            .filter_by(batch_id=test_batch.id)
            .order_by(BatchLog.timestamp)
            .all()
        )
        
        # Verify log types and messages in order
        assert logs[0].event_type == "PROFILE_CHECK"
        assert logs[0].profile_id == persisted_profile.id
        assert logs[0].profile.username == persisted_profile.username
        assert "has_story=True" in logs[0].message

        assert logs[1].event_type == "PROFILE_CHECK"
        assert logs[1].profile_id == persisted_profile.id
        assert logs[1].profile.username == persisted_profile.username
        assert "has_story=False" in logs[1].message

        assert logs[2].event_type == "PROFILE_ERROR"
        assert logs[2].profile_id == persisted_profile.id
        assert logs[2].profile.username == persisted_profile.username
        assert "Failed to check" in logs[2].message

@pytest.mark.real_db
def test_create_log_start_stop_pause_resume(app, db_session, test_batch):
    """Test logging of batch state transitions"""
    with app.app_context():
        # Test batch start
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="BATCH_START",
            message="Starting batch"
        )
        db_session.commit()

        # Add small delay between logs to ensure ordering
        import time
        time.sleep(0.1)

        # Test batch pause
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="BATCH_PAUSED",
            message="Batch paused"
        )
        db_session.commit()

        time.sleep(0.1)

        # Test batch resume
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="BATCH_RESUME",
            message="Resuming batch"
        )
        db_session.commit()

        time.sleep(0.1)

        # Test batch stop
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="BATCH_STOP",
            message="Batch stopped"
        )
        db_session.commit()

        # Verify logs were created
        logs, total = BatchLogService.get_logs(test_batch.id)
        assert total == 4

        # Get logs in chronological order (oldest first)
        logs = sorted(logs, key=lambda x: x.timestamp)
        log_types = [log.event_type for log in logs]
        
        # Verify log types in order
        assert log_types == ["BATCH_START", "BATCH_PAUSED", "BATCH_RESUME", "BATCH_STOP"]

@pytest.mark.real_db
def test_create_log_queue_movements(app, db_session, test_batch):
    """Test logging of batch queue position changes"""
    with app.app_context():
        # Test batch queued
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="BATCH_QUEUED",
            message="Batch added to queue at position 3"
        )
        db_session.commit()

        # Test position update
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="QUEUE_UPDATE",
            message="Batch moved from position 3 to 2"
        )
        db_session.commit()

        # Test promotion to running
        BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="QUEUE_UPDATE",
            message="Batch promoted to running position"
        )
        db_session.commit()

        # Verify logs were created
        logs, total = BatchLogService.get_logs(test_batch.id)
        assert total == 3

        # Verify log types and messages
        queued_log = next(log for log in logs if "added to queue" in log.message)
        assert queued_log.event_type == "BATCH_QUEUED"

        position_log = next(log for log in logs if "moved from position" in log.message)
        assert position_log.event_type == "QUEUE_UPDATE"

        promoted_log = next(log for log in logs if "promoted to running" in log.message)
        assert promoted_log.event_type == "QUEUE_UPDATE"