"""
Batch Processor Tests
Tests for batch processing functionality
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from core.batch_processor import BatchProcessor
from models import Batch, BatchProfile, Profile, Proxy, SystemSettings

@pytest.fixture
def batch_processor():
    """Create batch processor instance"""
    settings = SystemSettings.get_settings()
    return BatchProcessor(settings)

def test_process_batch(batch_processor, create_batch, create_profile, create_proxy):
    """Should process batch of profiles"""
    # Create test data
    batch = create_batch(None)  # No niche needed for test
    profiles = [create_profile(f'user{i}') for i in range(3)]
    proxies = [create_proxy(f'127.0.0.{i}', 8080) for i in range(2)]
    
    # Add profiles to batch
    for profile in profiles:
        BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
    
    # Process batch
    with patch('core.story_checker.check_instagram_story') as mock_check:
        # Simulate some stories found
        mock_check.side_effect = [
            {'has_story': True},   # First profile
            {'has_story': False},  # Second profile
            {'has_story': True}    # Third profile
        ]
        
        result = batch_processor.process_batch(batch)
        
        assert result['success'] is True
        assert result['total'] == 3
        assert result['completed'] == 3
        assert result['successful'] == 2  # Two stories found
        
        # Verify batch status
        batch = Batch.get_by_id(batch.id)
        assert batch.status == 'completed'
        assert batch.completed_profiles == 3
        assert batch.successful_checks == 2

def test_process_batch_with_errors(batch_processor, create_batch, create_profile, create_proxy):
    """Should handle errors during batch processing"""
    batch = create_batch(None)
    profiles = [create_profile(f'user{i}') for i in range(3)]
    proxy = create_proxy('127.0.0.1', 8080)
    
    for profile in profiles:
        BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
    
    with patch('core.story_checker.check_instagram_story') as mock_check:
        # Simulate mixed success/failure
        mock_check.side_effect = [
            {'has_story': True},           # Success
            Exception('API error'),        # Error
            {'has_story': False}           # Success
        ]
        
        result = batch_processor.process_batch(batch)
        
        assert result['success'] is True  # Batch completes despite errors
        assert result['total'] == 3
        assert result['completed'] == 2   # Two successful checks
        assert result['failed'] == 1      # One failed check
        
        # Verify batch status
        batch = Batch.get_by_id(batch.id)
        assert batch.status == 'completed'
        assert batch.failed_checks == 1

def test_process_batch_rate_limit(batch_processor, create_batch, create_profile, create_proxy):
    """Should handle rate limiting during batch processing"""
    batch = create_batch(None)
    profiles = [create_profile(f'user{i}') for i in range(3)]
    proxy = create_proxy('127.0.0.1', 8080)
    
    for profile in profiles:
        BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
    
    with patch('core.story_checker.check_instagram_story') as mock_check:
        # Simulate rate limit after first check
        mock_check.side_effect = [
            {'has_story': True},                    # Success
            Exception('Rate limited'),              # Rate limit
            {'has_story': False}                    # Success after retry
        ]
        
        result = batch_processor.process_batch(batch)
        
        assert result['success'] is True
        assert result['total'] == 3
        assert result['completed'] == 3
        assert 'rate_limited' in result
        assert result['rate_limited'] > 0  # Number of rate limits hit

def test_process_batch_proxy_rotation(batch_processor, create_batch, create_profile):
    """Should rotate proxies during batch processing"""
    batch = create_batch(None)
    profiles = [create_profile(f'user{i}') for i in range(3)]
    proxies = [
        Proxy(host=f'127.0.0.{i}', port=8080).save()
        for i in range(2)
    ]
    
    for profile in profiles:
        BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
    
    with patch('core.story_checker.check_instagram_story') as mock_check:
        mock_check.return_value = {'has_story': False}
        
        result = batch_processor.process_batch(batch)
        
        assert result['success'] is True
        
        # Verify proxies were used
        for proxy in proxies:
            proxy = Proxy.get_by_id(proxy.id)
            assert proxy.total_requests > 0

def test_process_batch_cancellation(batch_processor, create_batch, create_profile):
    """Should handle batch cancellation"""
    batch = create_batch(None)
    profiles = [create_profile(f'user{i}') for i in range(3)]
    
    for profile in profiles:
        BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
    
    # Cancel batch after first profile
    def mock_check(*args):
        if mock_check.calls == 0:
            mock_check.calls += 1
            return {'has_story': True}
        batch.status = 'cancelled'
        batch.save()
        return {'has_story': False}
    mock_check.calls = 0
    
    with patch('core.story_checker.check_instagram_story', side_effect=mock_check):
        result = batch_processor.process_batch(batch)
        
        assert result['success'] is True
        assert result['cancelled'] is True
        assert result['completed'] == 1  # Only first profile completed

def test_process_batch_concurrent(batch_processor, create_batch, create_profile):
    """Should process profiles concurrently"""
    batch = create_batch(None)
    profiles = [create_profile(f'user{i}') for i in range(5)]
    
    for profile in profiles:
        BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
    
    # Track concurrent executions
    running = 0
    max_running = 0
    
    def mock_check(*args):
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        # Simulate some work
        import time
        time.sleep(0.1)
        running -= 1
        return {'has_story': False}
    
    with patch('core.story_checker.check_instagram_story', side_effect=mock_check):
        settings = SystemSettings.get_settings()
        settings.max_threads = 3
        settings.save()
        
        result = batch_processor.process_batch(batch)
        
        assert result['success'] is True
        assert max_running <= 3  # Never exceeded max threads
