import json
import time
from flask import url_for
from models.batch import Batch
from models.niche import Niche
from models.profile import Profile
from unittest.mock import MagicMock, patch
from core.worker import WorkerPool
from core.batch_processor import process_batch
import pytest
import logging
import threading

def test_start_batches(client, app, db):
    logging.info("Starting test_start_batches")
    
    try:
        # Create a mock worker pool
        mock_worker_pool = MagicMock()
        mock_worker_pool.get_running_batch_ids.return_value = []  # No running batches
        app.worker_pool = mock_worker_pool
        logging.info("Created mock worker pool")

        # Create a test niche with a unique name
        import uuid
        unique_niche_name = f"Test Niche {uuid.uuid4()}"
        niche = Niche(name=unique_niche_name)
        db.session.add(niche)
        db.session.commit()
        logging.info(f"Created test niche: {niche.id} with name: {unique_niche_name}")

        # Create test profiles
        profile1 = Profile(username="test_user1", niche_id=niche.id)
        profile2 = Profile(username="test_user2", niche_id=niche.id)
        db.session.add_all([profile1, profile2])
        db.session.commit()
        logging.info(f"Created test profiles: {profile1.id}, {profile2.id}")

        # Create test batches
        batch1 = Batch(niche_id=niche.id, profile_ids=[profile1.id])
        batch2 = Batch(niche_id=niche.id, profile_ids=[profile2.id])
        db.session.add_all([batch1, batch2])
        db.session.commit()
        logging.info(f"Created test batches: {batch1.id}, {batch2.id}")

        # Attempt to start the batches
        logging.info("Attempting to start batches")
        response = client.post(
            url_for('api.batch.start_batches'),
            json={'batch_ids': [batch1.id, batch2.id]}
        )
        logging.info(f"Start batches response: {response.status_code}")
        logging.info(f"Response data: {response.data}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.data}"

        # Check if batches are now in progress
        db.session.refresh(batch1)
        db.session.refresh(batch2)
        logging.info(f"Updated batch statuses: {batch1.status}, {batch2.status}")

        assert batch1.status == 'in_progress', f"Expected batch1 status to be 'in_progress', got '{batch1.status}'"
        assert batch2.status == 'in_progress', f"Expected batch2 status to be 'in_progress', got '{batch2.status}'"

        # Check if WorkerPool.submit was called for each batch
        assert mock_worker_pool.submit.call_count == 2, f"Expected WorkerPool.submit to be called 2 times, but it was called {mock_worker_pool.submit.call_count} times"
        mock_worker_pool.submit.assert_any_call(process_batch, batch1.id)
        mock_worker_pool.submit.assert_any_call(process_batch, batch2.id)

        logging.info("Test completed successfully")
    except Exception as e:
        logging.error(f"Test failed with exception: {str(e)}")
        raise

def test_start_batches_with_running_batch(client, app, db):
    logging.info("Starting test_start_batches_with_running_batch")
    
    # Create a test niche
    niche = Niche(name="Test Niche")
    db.session.add(niche)
    db.session.commit()
    logging.info(f"Created test niche: {niche.id}")

    # Create test profiles
    profile1 = Profile(username="test_user3", niche_id=niche.id)
    profile2 = Profile(username="test_user4", niche_id=niche.id)
    db.session.add(profile1)
    db.session.add(profile2)
    db.session.commit()
    logging.info(f"Created test profiles: {profile1.id}, {profile2.id}")

    # Create test batches
    running_batch = Batch(niche_id=niche.id, profile_ids=[profile1.id])
    queued_batch = Batch(niche_id=niche.id, profile_ids=[profile2.id])
    db.session.add(running_batch)
    db.session.add(queued_batch)
    db.session.commit()
    logging.info(f"Created test batches: running_batch {running_batch.id}, queued_batch {queued_batch.id}")

    # Set the running_batch status to 'in_progress'
    running_batch.status = 'in_progress'
    db.session.commit()
    logging.info(f"Set running_batch status to 'in_progress'")

    # Mock the worker pool to simulate a running batch
    mock_worker_pool = MagicMock()
    mock_worker_pool.get_running_batch_ids.return_value = [running_batch.id]
    app.worker_pool = mock_worker_pool

    # Attempt to start the queued batch
    logging.info("Attempting to start the queued batch")
    response = client.post(
        url_for('api.batch.start_batches'),
        json={'batch_ids': [queued_batch.id]}
    )
    logging.info(f"Start batch response: {response.status_code}")

    assert response.status_code == 409, f"Expected 409, got {response.status_code}. Response: {response.data}"

    # Check if queued batch is still queued
    updated_queued_batch = db.session.get(Batch, queued_batch.id)
    logging.info(f"Updated queued batch status: {updated_queued_batch.status}")
    assert updated_queued_batch.status == 'queued', f"Expected queued batch status to remain 'queued', got '{updated_queued_batch.status}'"

    # Check response content
    response_data = response.get_json()
    logging.info(f"Response data: {response_data}")
    assert 'error' in response_data, "Expected 'error' key in response"
    assert 'Another batch is already running' in response_data['error'], "Expected error message about running batch"
    assert 'running_batch_ids' in response_data, "Expected 'running_batch_ids' key in response"
    assert running_batch.id in response_data['running_batch_ids'], "Expected running batch ID in 'running_batch_ids'"

    logging.info("Test completed successfully")
