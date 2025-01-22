"""
Batch API Routes
Handles batch operations endpoints
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import db, Batch
from services.story_service import cleanup_expired_stories
from services.queue_manager import QueueManager
from services.batch_log_service import BatchLogService
from config.logging_config import setup_blueprint_logging
from worker_manager import initialize_worker_pool
from core.batch_processor import process_batch
from services.queue_ordering import reorder_queue

batch_bp = Blueprint('batch', __name__)
logger = setup_blueprint_logging(batch_bp, 'batch')

@batch_bp.route('', methods=['GET'])
def list_batches():
    """List all batches"""
    try:
        # Explicitly join with niche to avoid lazy loading issues
        batches = Batch.query.join(Batch.niche).all()
        return jsonify([batch.to_dict() for batch in batches])
    except Exception as e:
        logger.error(f"Error listing batches: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@batch_bp.route('', methods=['POST'])
def create_batch():
    """Create new batch from selected profiles"""
    try:
        logger.info("=== Creating New Batch ===")
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Validate required fields
        logger.info("1. Validating request data...")
        if not data.get('niche_id'):
            return jsonify({'error': 'niche_id is required'}), 400

        profile_ids = data.get('profile_ids')
        if not profile_ids:
            return jsonify({'error': 'profile_ids is required'}), 400
        if not isinstance(profile_ids, list) or len(profile_ids) == 0:
            return jsonify({'error': 'profile_ids must be a non-empty list'}), 400

        # Create batch
        logger.info("2. Creating batch...")
        batch = Batch(niche_id=data['niche_id'], profile_ids=profile_ids)
        db.session.add(batch)

        # Check if position 0 is available
        logger.info("3. Checking queue position...")
        running_batch = QueueManager.get_running_batch()
        if not running_batch:
            # Initialize position 0 but keep as queued until processing starts
            logger.info("4. Position 0 available, preparing to start batch...")
            batch.status = 'queued'
            batch.queue_position = 0
        else:
            # Queue this batch
            logger.info("4. Position 0 taken, queueing batch...")
            batch.status = 'queued'
            batch.queue_position = QueueManager.get_next_position()

        # Commit the batch first to avoid foreign key violations
        db.session.commit()

        # Now create logs after batch is committed
        BatchLogService.create_log(batch.id, 'INFO', f'Created batch with {len(profile_ids)} profiles')

        # Define the done_callback function outside the if block
        def done_callback(future):
            try:
                result = future.result()
                logger.info(f"Batch {batch.id} processed successfully")
            except Exception as e:
                logger.error(f"Error processing batch {batch.id}: {str(e)}")
                BatchLogService.create_log(batch.id, 'ERROR', f'Error processing batch: {str(e)}')

        if not running_batch:
            BatchLogService.create_log(batch.id, 'INFO', f'Assigned queue position 0')

            if not hasattr(current_app, 'worker_pool'):
                logger.info("5. Initializing worker pool...")
                initialize_worker_pool(current_app, db)
                BatchLogService.create_log(batch.id, 'INFO', f'Initialized worker pool')

            logger.info("6. Registering batch with worker pool...")
            current_app.worker_pool.register_batch(batch.id)
            BatchLogService.create_log(batch.id, 'INFO', f'Registered with worker pool')

            logger.info("7. Submitting batch for processing...")

            # Submit the batch processing task with the done_callback
            future = current_app.worker_pool.submit(process_batch, batch.id)
            future.add_done_callback(done_callback)
            BatchLogService.create_log(batch.id, 'INFO', f'Submitted for processing')
        else:
            BatchLogService.create_log(batch.id, 'INFO', f'Queued at position {batch.queue_position}')

        logger.info("8. Batch creation complete")
        return jsonify(batch.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating batch: {str(e)}")
        return jsonify({'error': 'Failed to create batch', 'details': str(e)}), 500

@batch_bp.route('/start', methods=['POST'])
def start_batches():
    """Start selected batches"""
    try:
        logger.info("=== Starting Batches ===")
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        # Initialize worker pool if needed
        logger.info("1. Checking worker pool...")
        if not hasattr(current_app, 'worker_pool'):
            logger.info("2. Initializing worker pool...")
            initialize_worker_pool(current_app, db)

        # Check if position 0 is taken
        logger.info("3. Checking queue position...")
        if QueueManager.get_running_batch():
            return jsonify({'error': 'Another batch is already running'}), 409

        # Get batches to start
        logger.info("4. Getting batches to start...")
        clean_ids = [id.strip() for id in data['batch_ids']]
        batches = Batch.query.filter(Batch.id.in_(clean_ids)).all()
        if not batches:
            return jsonify({'error': 'No batches found with the provided IDs'}), 404

        # Start first batch, queue others
        logger.info("5. Processing batches...")
        for i, batch in enumerate(batches):
            if i == 0:  # First batch gets position 0
                logger.info(f"6. Starting batch {batch.id}...")
                batch.status = 'queued'  # Keep as queued until processing starts
                batch.queue_position = 0
                current_app.worker_pool.register_batch(batch.id)
                current_app.worker_pool.submit(process_batch, batch.id)
                BatchLogService.create_log(batch.id, 'INFO', f'Starting batch {batch.id}')
            else:  # Queue remaining batches
                logger.info(f"6. Queueing batch {batch.id}...")
                batch.status = 'queued'
                batch.queue_position = QueueManager.get_next_position()
                BatchLogService.create_log(batch.id, 'INFO', f'Queued at position {batch.queue_position}')

        db.session.commit()
        logger.info("7. Batch start process complete")
        return jsonify([batch.to_dict() for batch in batches])

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting batches: {str(e)}")
        return jsonify({'error': 'Failed to start batches', 'details': str(e)}), 500

@batch_bp.route('/stop', methods=['POST'])
def stop_batches():
    """Stop selected batches"""
    try:
        logger.info("=== Stopping Batches ===")
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        # Initialize worker pool if needed
        logger.info("1. Checking worker pool...")
        if not hasattr(current_app, 'worker_pool'):
            logger.info("2. Initializing worker pool...")
            initialize_worker_pool(current_app, db)

        # Get batches to stop
        logger.info("3. Getting batches to stop...")
        clean_ids = [id.strip() for id in data['batch_ids']]
        batches = Batch.query.filter(Batch.id.in_(clean_ids)).all()
        if not batches:
            return jsonify({'error': 'No batches found with the provided IDs'}), 404

        # Stop and requeue batches
        logger.info("4. Processing batches...")
        for batch in batches:
            if batch.queue_position == 0:  # Only stop running batch
                logger.info(f"5. Stopping batch {batch.id}...")
                current_app.worker_pool.unregister_batch(batch.id)
                QueueManager.move_to_end(batch)
                BatchLogService.create_log(batch.id, 'INFO', f'Stopped batch {batch.id}')

        # Promote next batch if needed
        logger.info("6. Checking for next batch...")
        if not QueueManager.get_running_batch():
            logger.info("7. Promoting next batch...")
            QueueManager.promote_next_batch()

        logger.info("8. Batch stop process complete")
        return jsonify([batch.to_dict() for batch in batches])

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error stopping batches: {str(e)}")
        return jsonify({'error': 'Failed to stop batches', 'details': str(e)}), 500

@batch_bp.route('', methods=['DELETE'])
def delete_batches():
    """Delete selected batches"""
    try:
        logger.info("=== Deleting Batches ===")
        data = request.get_json(force=True)
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        # Initialize worker pool if needed
        logger.info("1. Checking worker pool...")
        if not hasattr(current_app, 'worker_pool'):
            logger.info("2. Initializing worker pool...")
            initialize_worker_pool(current_app, db)

        # Get batches to delete
        logger.info("3. Getting batches to delete...")
        clean_ids = [id.strip() for id in data['batch_ids']]
        batches = Batch.query.filter(Batch.id.in_(clean_ids)).all()
        if not batches:
            return jsonify({'error': 'No batches found with the provided IDs'}), 404

        # Delete batches
        logger.info("4. Processing batches...")
        for batch in batches:
            if batch.queue_position == 0:  # Only unregister running batch
                logger.info(f"5. Unregistering batch {batch.id}...")
                current_app.worker_pool.unregister_batch(batch.id)
                BatchLogService.create_log(batch.id, 'INFO', f'Deleted batch {batch.id}')
            logger.info(f"6. Deleting batch {batch.id}...")
            db.session.delete(batch)

        db.session.commit()

        # Reorder queue and promote next batch if needed
        logger.info("7. Reordering queue...")
        reorder_queue()  # Call the reorder_queue function directly
        if not QueueManager.get_running_batch():
            logger.info("8. Promoting next batch...")
            QueueManager.promote_next_batch()

        logger.info("9. Batch deletion complete")
        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting batches: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@batch_bp.route('/<string:batch_id>/logs', methods=['GET'])
def get_batch_logs(batch_id):
    """Get logs for a specific batch"""
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        # Convert start_time and end_time to datetime objects if provided
        if start_time:
            start_time = datetime.fromisoformat(start_time)
        if end_time:
            end_time = datetime.fromisoformat(end_time)

        logs, total = BatchLogService.get_logs(batch_id, start_time, end_time, limit, offset)

        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use ISO 8601 format.'}), 400
    except Exception as e:
        logger.error(f"Error retrieving batch logs: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
