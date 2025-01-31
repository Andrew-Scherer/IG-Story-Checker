"""
Test batch log service functionality
"""

import pytest
from datetime import datetime, timedelta, UTC
from models import db
from models.batch import Batch
from models.batch_log import BatchLog
from models.profile import Profile
from models.proxy import Proxy
from models.niche import Niche
from services.batch_log_service import BatchLogService
import uuid

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

def test_create_log_with_profile(app, db_session, test_batch, test_profile):
    """Test log creation with profile reference"""
    with app.app_context():
        # Create log with profile
        log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="PROFILE_EVENT",
            message="Test profile log",
            profile_id=test_profile.id
        )
        db_session.commit()

        # Verify log and relationship
        saved_log = db_session.query(BatchLog).filter_by(id=log.id).first()
        assert saved_log.profile_id == test_profile.id
        assert saved_log.profile == test_profile

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

def test_get_logs_with_time_filter(app, db_session, test_batch):
    """Test log retrieval with time filtering"""
    with app.app_context():
        # Create logs at different times
        now = datetime.now(UTC)
        
        # Old log
        old_log = BatchLog(
            batch_id=test_batch.id,
            event_type="OLD_EVENT",
            message="Old message",
            timestamp=now - timedelta(hours=2)
        )
        db_session.add(old_log)
        
        # Recent log
        recent_log = BatchLog(
            batch_id=test_batch.id,
            event_type="RECENT_EVENT",
            message="Recent message",
            timestamp=now - timedelta(minutes=30)
        )
        db_session.add(recent_log)
        db_session.commit()

        # Test time filtering
        start_time = now - timedelta(hours=1)
        logs, total = BatchLogService.get_logs(
            test_batch.id,
            start_time=start_time
        )
        assert total == 1
        assert logs[0].event_type == "RECENT_EVENT"

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

def test_log_persistence(app, db_session, test_batch):
    """Test log persistence and relationship loading"""
    with app.app_context():
        # Create log
        log = BatchLogService.create_log(
            batch_id=test_batch.id,
            event_type="TEST_EVENT",
            message="Test message"
        )
        db_session.commit()
        log_id = log.id

        # Clear session and reload
        db_session.expunge_all()
        
        # Verify log can be retrieved
        reloaded_log = db_session.query(BatchLog).get(log_id)
        assert reloaded_log is not None
        assert reloaded_log.batch == test_batch

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