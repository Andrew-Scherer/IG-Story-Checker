"""
End-to-end tests for batch workflow
"""

import pytest
from playwright.sync_api import expect
from models import db, Profile, Batch, Niche

def test_complete_workflow(page, test_server, db_session):
    """Test complete workflow from profile selection to batch completion"""
    # Create test data
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.commit()

    profiles = [
        Profile(username=f'test{i}', niche_id=niche.id, status='active')
        for i in range(3)
    ]
    db_session.add_all(profiles)
    db_session.commit()

    # Navigate to app
    page.goto('http://localhost:3000')

    # Verify initial state
    expect(page.get_by_text('Niche Feed')).to_be_visible()
    expect(page.get_by_text('Test Niche')).to_be_visible()

    # Select niche
    page.click('text=Test Niche')
    expect(page.get_by_text('test0')).to_be_visible()
    expect(page.get_by_text('test1')).to_be_visible()
    expect(page.get_by_text('test2')).to_be_visible()

    # Select profiles
    page.get_by_role('checkbox').nth(1).click()  # First profile
    page.get_by_role('checkbox').nth(2).click()  # Second profile

    # Verify button state
    check_stories_button = page.get_by_text('Check Selected Profiles for Stories (2)')
    expect(check_stories_button).to_be_enabled()

    # Create batch
    check_stories_button.click()

    # Switch to Batch tab
    page.click('text=Batch')

    # Verify batch created
    expect(page.get_by_text('Test Niche')).to_be_visible()
    expect(page.get_by_text('0/2')).to_be_visible()
    expect(page.get_by_text('queued')).to_be_visible()

    # Select and start batch
    page.get_by_role('checkbox').nth(1).click()
    page.click('text=Start Selected')

    # Verify processing started
    expect(page.get_by_text('in_progress')).to_be_visible()

    # Wait for completion (with timeout)
    expect(page.get_by_text('done')).to_be_visible(timeout=30000)

    # Verify final state
    expect(page.get_by_text('2/2')).to_be_visible()

    # Switch back to Niche Feed
    page.click('text=Niche Feed')

    # Verify profile updates
    for profile in profiles[:2]:  # Only check selected profiles
        profile = Profile.query.get(profile.id)
        assert profile.total_checks == 1

def test_error_handling(page, test_server, db_session, mocker):
    """Test error handling in workflow"""
    # Mock story checker to simulate errors
    mocker.patch('core.story_checker.StoryChecker.check_profile', side_effect=Exception("Network error"))

    # Create test data
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.commit()

    profile = Profile(username='test1', niche_id=niche.id, status='active')
    db_session.add(profile)
    db_session.commit()

    # Navigate to app
    page.goto('http://localhost:3000')

    # Select niche and profile
    page.click('text=Test Niche')
    page.get_by_role('checkbox').nth(1).click()

    # Create batch
    page.get_by_text('Check Selected Profiles for Stories (1)').click()

    # Switch to Batch tab
    page.click('text=Batch')

    # Start batch
    page.get_by_role('checkbox').nth(1).click()
    page.click('text=Start Selected')

    # Verify error handling
    expect(page.get_by_text('queued')).to_be_visible()  # Should reset to queued on error

def test_status_updates(page, test_server, db_session):
    """Test UI updates during processing"""
    # Create test data
    niche = Niche(name='Test Niche')
    db_session.add(niche)
    db_session.commit()

    profiles = [
        Profile(username=f'test{i}', niche_id=niche.id, status='active')
        for i in range(5)
    ]
    db_session.add_all(profiles)
    db_session.commit()

    # Navigate to app
    page.goto('http://localhost:3000')

    # Create batch with all profiles
    page.click('text=Test Niche')
    page.get_by_role('checkbox').nth(0).click()  # Select all
    page.get_by_text('Check Selected Profiles for Stories (5)').click()

    # Switch to Batch tab
    page.click('text=Batch')

    # Start batch
    page.get_by_role('checkbox').nth(1).click()
    page.click('text=Start Selected')

    # Verify progress updates
    expect(page.get_by_text('0/5')).to_be_visible()
    expect(page.get_by_text('in_progress')).to_be_visible()

    # Wait for updates
    expect(page.get_by_text('2/5')).to_be_visible(timeout=10000)
    expect(page.get_by_text('5/5')).to_be_visible(timeout=30000)
    expect(page.get_by_text('done')).to_be_visible()
