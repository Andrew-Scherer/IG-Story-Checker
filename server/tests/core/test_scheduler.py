"""
Scheduler Tests
Tests for automatic batch scheduling functionality
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from core.scheduler import BatchScheduler
from models import Niche, Batch, StoryResult, SystemSettings

@pytest.fixture
def scheduler():
    """Create scheduler instance"""
    settings = SystemSettings.get_settings()
    return BatchScheduler(settings)

def test_check_niche_targets(scheduler, create_niche, create_profile, create_story):
    """Should identify niches below story target"""
    # Create test data
    niche = create_niche('Fitness', daily_story_target=5)
    profiles = [create_profile(f'user{i}', niche_id=niche.id) for i in range(3)]
    
    # Create some active stories
    for profile in profiles[:2]:  # Only 2 stories, below target of 5
        create_story(profile.id, None)
    
    needs_batch = scheduler.check_niche_targets()
    assert len(needs_batch) == 1
    assert needs_batch[0].id == niche.id

def test_check_niche_at_target(scheduler, create_niche, create_profile, create_story):
    """Should skip niches at or above target"""
    niche = create_niche('Fitness', daily_story_target=3)
    profiles = [create_profile(f'user{i}', niche_id=niche.id) for i in range(3)]
    
    # Create stories meeting target
    for profile in profiles:  # All 3 have stories, meeting target
        create_story(profile.id, None)
    
    needs_batch = scheduler.check_niche_targets()
    assert len(needs_batch) == 0

def test_check_niche_with_active_batch(scheduler, create_niche, create_batch):
    """Should skip niches with active batches"""
    niche = create_niche('Fitness', daily_story_target=5)
    
    # Create active batch
    batch = create_batch(niche.id)
    batch.status = 'running'
    batch.save()
    
    needs_batch = scheduler.check_niche_targets()
    assert len(needs_batch) == 0

def test_trigger_batches(scheduler, create_niche):
    """Should trigger batches for niches below target"""
    niches = [
        create_niche('Fitness', daily_story_target=5),
        create_niche('Fashion', daily_story_target=3)
    ]
    
    with patch('core.batch_processor.BatchProcessor.process_batch') as mock_process:
        triggered = scheduler.trigger_batches(niches)
        
        assert len(triggered) == 2
        assert all(b.status == 'pending' for b in triggered)
        assert mock_process.call_count == 2

def test_scheduler_interval(scheduler):
    """Should respect minimum trigger interval"""
    settings = SystemSettings.get_settings()
    settings.min_trigger_interval = 60  # 60 minutes
    settings.save()
    
    # Mock recent batch
    recent_batch = Batch(niche_id='test')
    recent_batch.start_time = datetime.utcnow() - timedelta(minutes=30)
    recent_batch.save()
    
    can_trigger = scheduler.check_trigger_interval(recent_batch.niche_id)
    assert can_trigger is False

def test_expired_story_cleanup(scheduler, create_profile, create_story):
    """Should clean up expired story results"""
    profile = create_profile('testuser')
    
    # Create expired story
    story = create_story(profile.id, None)
    story.expires_at = datetime.utcnow() - timedelta(hours=1)
    story.save()
    
    cleaned = scheduler.cleanup_expired_stories()
    assert cleaned == 1
    
    # Verify story removed
    assert StoryResult.query.get(story.id) is None

def test_scheduler_disabled(scheduler, create_niche):
    """Should respect auto-trigger setting"""
    settings = SystemSettings.get_settings()
    settings.auto_trigger_enabled = False
    settings.save()
    
    niche = create_niche('Fitness', daily_story_target=5)
    
    triggered = scheduler.run()
    assert len(triggered) == 0
