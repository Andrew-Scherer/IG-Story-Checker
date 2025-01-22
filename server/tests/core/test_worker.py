import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, UTC
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models.batch import BatchProfile
from models.proxy import Proxy
from models.session import Session
from models.profile import Profile
from core.worker.worker import Worker
from core.story_checker import StoryChecker
from core.worker.worker_state import WorkerState
from models.settings import SystemSettings

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, UTC
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models.batch import BatchProfile
from models.proxy import Proxy
from models.session import Session
from models.profile import Profile
from core.worker.worker import Worker
from core.story_checker import StoryChecker
from core.worker.worker_state import WorkerState
from models.settings import SystemSettings

@pytest.fixture(scope='module')
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

@pytest.fixture(scope='module')
def db(app):
    db = SQLAlchemy(app)
    with app.app_context():
        db.create_all()
    return db

@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield

@pytest.fixture(autouse=True)
def mock_system_settings():
    with patch('models.settings.SystemSettings.get_settings') as mock_get_settings:
        mock_settings = Mock(spec=SystemSettings, proxy_max_failures=5)
        mock_get_settings.return_value = mock_settings
        yield mock_settings

@pytest.fixture
def mock_proxy():
    return Mock(spec=Proxy, id=1, host='127.0.0.1', port=8080)

@pytest.fixture
def mock_session():
    return Mock(spec=Session, id=1, session='test_session')

@pytest.fixture
def mock_profile():
    return Mock(spec=Profile, id=1, username='test_user', total_checks=0, total_detections=0)

@pytest.fixture
def mock_batch_profile(mock_profile):
    return Mock(spec=BatchProfile, id=1, profile=mock_profile)

@pytest.fixture
def worker(mock_proxy, mock_session):
    worker = Worker(mock_proxy, mock_session)
    worker.state = MockWorkerState()
    return worker

class MockWorkerState(WorkerState):
    def __init__(self):
        super().__init__()
        self._disabled = False
        self._rate_limited = False

    def disable(self):
        self._disabled = True

    def enable(self):
        self._disabled = False

    @property
    def is_disabled(self):
        return self._disabled

    @is_disabled.setter
    def is_disabled(self, value):
        self._disabled = value

    @property
    def is_rate_limited(self):
        return self._rate_limited

    @is_rate_limited.setter
    def is_rate_limited(self, value):
        self._rate_limited = value

    def record_error(self, is_rate_limit: bool):
        super().record_error(is_rate_limit)
        if is_rate_limit:
            self.is_rate_limited = True

    def clear_rate_limit(self):
        self.is_rate_limited = False

    def check_rate_limit(self) -> bool:
        return self.is_rate_limited

@pytest.mark.asyncio
class TestWorker:
    async def test_worker_state_methods(self):
        state = MockWorkerState()
        assert hasattr(state, 'disable'), "WorkerState should have a 'disable' method"
        assert hasattr(state, 'enable'), "WorkerState should have an 'enable' method"

    async def test_worker_initialization(self, worker, mock_proxy, mock_session):
        assert worker.proxy_session.proxy == mock_proxy
        assert worker.proxy_session.session == mock_session
        assert isinstance(worker.story_checker, StoryChecker)
        assert worker.current_profile is None
        assert worker.last_check is None

    async def test_worker_check_story_success(self, worker, mock_batch_profile):
        worker.story_checker.check_story = AsyncMock(return_value=True)
        worker.state.check_rate_limit = Mock(return_value=False)
        success, has_story = await worker.check_story(mock_batch_profile)
        assert success is True
        assert has_story is True
        assert mock_batch_profile.status == 'completed'
        assert mock_batch_profile.has_story is True
        assert mock_batch_profile.processed_at is not None
        assert mock_batch_profile.proxy_id == worker.proxy_session.proxy.id
        assert mock_batch_profile.error is None

    async def test_worker_check_story_failure(self, worker, mock_batch_profile):
        worker.story_checker.check_story = AsyncMock(side_effect=Exception("Test error"))
        success, has_story = await worker.check_story(mock_batch_profile)
        assert success is False
        assert has_story is False
        assert mock_batch_profile.status == 'failed'
        assert mock_batch_profile.error is not None

    async def test_worker_rate_limit_handling(self, worker, mock_batch_profile):
        worker.story_checker.check_story = AsyncMock(side_effect=Exception("Rate limited"))
        success, has_story = await worker.check_story(mock_batch_profile)
        assert success is False
        assert has_story is False
        assert worker.is_rate_limited is True
        assert mock_batch_profile.status == 'failed'
        assert "Rate limited" in mock_batch_profile.error

    async def test_worker_respects_minimum_interval(self, worker, mock_batch_profile):
        worker.story_checker.check_story = AsyncMock(return_value=True)
        worker.last_check = datetime.now(UTC) - timedelta(seconds=10)
        with patch('asyncio.sleep') as mock_sleep:
            await worker.check_story(mock_batch_profile)
            mock_sleep.assert_called_once_with(pytest.approx(10, abs=1))

    async def test_worker_cleanup(self, worker, mock_batch_profile):
        worker.story_checker.cleanup = AsyncMock()
        worker.story_checker.check_story = AsyncMock(return_value=True)
        await worker.check_story(mock_batch_profile)
        worker.story_checker.cleanup.assert_called_once()

    async def test_worker_availability(self, worker):
        assert worker.is_available() is True
        worker.state.disable()
        assert worker.is_available() is False
        worker.state.enable()
        worker.state.record_error(is_rate_limit=True)
        assert worker.is_available() is False
        worker.clear_rate_limit()
        assert worker.is_available() is True

    async def test_pre_check_validations(self, worker, mock_batch_profile):
        assert worker._pre_check_validations(mock_batch_profile) is True
        worker.state.disable()
        assert worker._pre_check_validations(mock_batch_profile) is False
        assert mock_batch_profile.error is not None
        worker.state.enable()
        worker.state.record_error(is_rate_limit=True)
        assert worker._pre_check_validations(mock_batch_profile) is False
        assert mock_batch_profile.error is not None

    async def test_enforce_minimum_interval(self, worker):
        worker.last_check = None
        await worker._enforce_minimum_interval()
        assert worker.last_check is None
        now = datetime.now(UTC)
        worker.last_check = now - timedelta(seconds=10)
        with patch('asyncio.sleep') as mock_sleep:
            await worker._enforce_minimum_interval()
            mock_sleep.assert_called_once_with(pytest.approx(10, abs=1))

    async def test_process_success_result(self, worker, mock_batch_profile):
        worker._process_success_result(mock_batch_profile, True)
        assert mock_batch_profile.status == 'completed'
        assert mock_batch_profile.has_story is True
        assert mock_batch_profile.processed_at is not None
        assert mock_batch_profile.proxy_id == worker.proxy_session.proxy.id
        assert mock_batch_profile.error is None
        assert mock_batch_profile.profile.total_checks == 1
        assert mock_batch_profile.profile.total_detections == 1
        assert mock_batch_profile.profile.active_story is True

    async def test_handle_error(self, worker, mock_batch_profile):
        success, has_story = worker._handle_error(mock_batch_profile, Exception("Test error"))
        assert success is False
        assert has_story is False
        assert mock_batch_profile.status == 'failed'
        assert mock_batch_profile.error is not None
        success, has_story = worker._handle_error(mock_batch_profile, Exception("Rate limited"))
        assert success is False
        assert has_story is False
        assert worker.is_rate_limited is True

if __name__ == '__main__':
    pytest.main()
