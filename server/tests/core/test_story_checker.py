"""
Test Story Checker
Tests API-based Instagram story checking
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, UTC, timedelta
from core.story_checker import SimpleStoryChecker, BrowserRateLimiter, StoryChecker, ProxySessionPair
import aiohttp
import json

# Mark all tests as async except for test_proxy_session_pair
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.filterwarnings("ignore::pytest.PytestWarning")
]

@pytest_asyncio.fixture
async def mock_session():
    """Create mock aiohttp session"""
    # Create the response object
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock()
    mock_response.text = AsyncMock()
    
    # Create the session with async close method
    session = Mock()
    session.close = AsyncMock()
    
    # Create an async context manager class
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_response
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None
    
    # Configure session.get to return the async context manager
    session.get = Mock(return_value=AsyncContextManager())
    
    return session, mock_response

@pytest_asyncio.fixture
async def story_checker(mock_session):
    """Create story checker for testing"""
    session, _ = mock_session
    checker = SimpleStoryChecker(
        proxy="http://test.proxy:8080",
        session_cookie="test_session_123"
    )
    checker.session = session
    return checker

@pytest_asyncio.fixture
async def rate_limiter():
    """Create rate limiter for testing"""
    return BrowserRateLimiter()

@pytest_asyncio.fixture
def proxy_session_pair():
    """Create proxy-session pair for testing"""
    return ProxySessionPair("http://test.proxy:8080", "test_session_123")

async def test_session_initialization():
    """Test session initialization"""
    with patch('aiohttp.ClientSession') as mock_session:
        checker = SimpleStoryChecker(
            proxy="http://test.proxy:8080",
            session_cookie="test_session_123"
        )
        await checker.initialize()
        
        mock_session.assert_called_once()
        assert checker.session is not None
        assert 'sessionid=test_session_123' in checker.headers['Cookie']

async def test_story_detection_success(story_checker, mock_session):
    """Test successful story detection"""
    _, response = mock_session
    
    # Mock profile response
    response.json.side_effect = [
        # First response: profile info
        {
            "data": {
                "user": {
                    "id": "12345"
                }
            }
        },
        # Second response: stories data
        {
            "reels": {
                "12345": {
                    "id": "12345",
                    "items": ["story1", "story2"]
                }
            }
        }
    ]
    
    # Check story
    has_story = await story_checker.check_story("test_user")
    
    assert has_story is True
    assert story_checker.last_check is not None

async def test_story_detection_no_story(story_checker, mock_session):
    """Test when no story is found"""
    _, response = mock_session
    
    # Mock profile response
    response.json.side_effect = [
        # First response: profile info
        {
            "data": {
                "user": {
                    "id": "12345"
                }
            }
        },
        # Second response: no stories
        {
            "reels": {}
        }
    ]
    
    # Check story
    has_story = await story_checker.check_story("test_user")
    
    assert has_story is False

async def test_rate_limit_detection(story_checker, mock_session):
    """Test rate limit detection"""
    _, response = mock_session
    response.status = 429
    
    with pytest.raises(Exception) as exc:
        await story_checker.check_story("test_user")
    
    assert "Rate limited" in str(exc.value)

async def test_invalid_response(story_checker, mock_session):
    """Test invalid API response handling"""
    _, response = mock_session
    
    # Mock invalid JSON response
    response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    
    with pytest.raises(Exception) as exc:
        await story_checker.check_story("test_user")
    
    assert "Failed to parse response" in str(exc.value)

async def test_network_error(story_checker, mock_session):
    """Test network error handling"""
    session, _ = mock_session
    session.get.side_effect = aiohttp.ClientError("Network error")
    
    with pytest.raises(Exception) as exc:
        await story_checker.check_story("test_user")
    
    assert "Network error" in str(exc.value)

async def test_rate_limiter_tracking(rate_limiter):
    """Test rate limit tracking"""
    proxy = "http://test.proxy:8080"
    
    # Should allow first visit
    assert rate_limiter.can_visit(proxy) is True
    
    # Record visit
    rate_limiter.record_visit(proxy)
    
    # Test visits with proper delays
    for i in range(10):  # Test fewer visits for speed
        # Set all previous visits to be old enough
        if proxy in rate_limiter.visits:
            rate_limiter.visits[proxy] = [
                t - timedelta(seconds=6)
                for t in rate_limiter.visits[proxy]
            ]
        
        assert rate_limiter.can_visit(proxy) is True
        rate_limiter.record_visit(proxy)

async def test_rate_limiter_cooldown(rate_limiter):
    """Test rate limit cooldown"""
    proxy = "http://test.proxy:8080"
    
    # Trigger rate limit
    rate_limiter.handle_rate_limit(proxy)
    
    # Should deny visits during cooldown
    assert rate_limiter.can_visit(proxy) is False
    
    # Mock cooldown expiration
    rate_limiter.cooldowns[proxy] = datetime.now(UTC)
    
    # Should allow visits after cooldown
    assert rate_limiter.can_visit(proxy) is True

def test_proxy_session_pair():
    """Test proxy-session pair functionality"""
    pair = ProxySessionPair("http://test.proxy:8080", "test_session_123")
    
    # Test initial state
    assert pair.success_rate == 1.0
    assert pair.total_checks == 0
    assert not pair.is_on_cooldown()
    
    # Test success tracking
    pair.record_success()
    assert pair.success_rate == 1.0
    assert pair.total_checks == 1
    
    # Test failure tracking
    pair.record_failure()
    assert pair.success_rate == 0.5  # 1 success out of 2 checks
    assert pair.total_checks == 2
    
    # Test cooldown
    pair.set_cooldown(minutes=15)
    assert pair.is_on_cooldown()
    
    # Test cooldown expiration
    pair.cooldown_until = datetime.now(UTC)
    assert not pair.is_on_cooldown()

async def test_story_checker_integration(mock_session):
    """Test full story checker flow with proxy-session pair"""
    session, response = mock_session
    
    # Create story checker
    checker = StoryChecker(
        proxy="http://test.proxy:8080",
        session_cookie="test_session_123"
    )
    await checker.checker.initialize()  # Initialize first
    checker.checker.session = session  # Then replace session
    
    # Mock successful story detection
    response.json.side_effect = [
        {"data": {"user": {"id": "12345"}}},
        {"reels": {"12345": {"items": ["story1"]}}}
    ]
    
    # Check story
    has_story = await checker.check_profile("test_user")
    
    assert has_story is True
    assert checker.checker.last_check is not None
    assert checker.pair.total_checks == 1
    assert checker.pair.success_rate == 1.0
    assert "http://test.proxy:8080" in checker.rate_limiter.visits

async def test_cleanup(story_checker):
    """Test cleanup"""
    await story_checker.cleanup()
    assert story_checker.session is None
