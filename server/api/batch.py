"""
Batch API Routes
Handles batch operations endpoints
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import db, Batch, BatchProfile
from services.story_service import cleanup_expired_stories
from services.queue_manager import QueueManager
from services.batch_state_manager import BatchStateManager
from services.batch_log_service import BatchLogService
from worker_manager import initialize_worker_pool
from config.logging_config import setup_blueprint_logging

batch_bp = Blueprint('batch', __name__)
logger = setup_blueprint_logging(batch_bp, 'batch')

# Initialize managers
state_manager = BatchStateManager()
queue_manager = QueueManager()
queue_manager.state_manager = state_manager

@batch_bp.route('', methods=['GET'])
def list_batches():
    """List all batches"""
    try:
        # Join with niche and eagerly load profiles with their relationships
        batches = (
            Batch.query
            .join(Batch.niche)
            .options(
                db.joinedload(Batch.niche),
                db.joinedload(Batch.profiles).joinedload(BatchProfile.profile)
            )
            .all()
        )
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
        running_batch = queue_manager.get_running_batch()
        if not running_batch:
            # Initialize position 0 but keep as queued until processing starts
            logger.info("4. Position 0 available, preparing to start batch...")
            queue_manager.state_manager.transition_state(batch, 'queued', 0)
        else:
            # Queue this batch
            logger.info("4. Position 0 taken, queueing batch...")
            next_pos = queue_manager.get_next_position()
            queue_manager.state_manager.transition_state(batch, 'queued', next_pos)

        # Commit the batch
        db.session.commit()

        # Now create logs after batch is committed
        BatchLogService.create_log(batch.id, 'INFO', f'Created batch with {len(profile_ids)} profiles')

        if not running_batch:
            if not hasattr(current_app, 'worker_pool'):
                logger.info("5. Initializing worker pool...")
                initialize_worker_pool(current_app, db)

            logger.info("6. Submitting batch for processing...")
            current_app.worker_pool.submit(queue_manager.execution_manager.process_batch, batch.id)
            BatchLogService.create_log(batch.id, 'INFO', f'Submitted for processing')

        logger.info("7. Batch creation complete")
        return jsonify(batch.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating batch: {str(e)}")
        return jsonify({'error': 'Failed to create batch', 'details': str(e)}), 500

@batch_bp.route('/resume', methods=['POST'])
def resume_batches():
    """Resume paused batches"""
    try:
        logger.info("=== Resuming Paused Batches ===")
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        # Initialize worker pool if needed
        logger.info("1. Checking worker pool...")
        if not hasattr(current_app, 'worker_pool'):
            logger.info("2. Initializing worker pool...")
            initialize_worker_pool(current_app, db)

        # Get batches to resume
        logger.info("3. Getting batches to resume...")
        clean_ids = [id.strip() for id in data['batch_ids']]
        batches = Batch.query.filter(
            Batch.id.in_(clean_ids),
            Batch.status == 'paused'
        ).all()
        if not batches:
            return jsonify({'error': 'No paused batches found with the provided IDs'}), 404

        # Resume batches
        logger.info("4. Processing batches...")
        results = []
        for i, batch in enumerate(batches):
            # First batch gets position 0, others get next position
            position = 0 if i == 0 else queue_manager.get_next_position()
            
            if queue_manager.state_manager.transition_state(batch, 'in_progress', position):
                if position == 0:
                    current_app.worker_pool.submit(queue_manager.execution_manager.process_batch, batch.id)
                results.append(batch.to_dict())

        db.session.commit()
        logger.info("5. Batch resume process complete")
        return jsonify(results)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resuming batches: {str(e)}")
        return jsonify({'error': 'Failed to resume batches', 'details': str(e)}), 500

@batch_bp.route('/stop', methods=['POST'])
def stop_batches():
    """Pause selected batches"""
    try:
        logger.info("=== Pausing Batches ===")
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        # Initialize worker pool if needed
        logger.info("1. Checking worker pool...")
        if not hasattr(current_app, 'worker_pool'):
            logger.info("2. Initializing worker pool...")
            initialize_worker_pool(current_app, db)

        # Get batches to pause
        logger.info("3. Getting batches to pause...")
        clean_ids = [id.strip() for id in data['batch_ids']]
        batches = Batch.query.filter(Batch.id.in_(clean_ids)).all()
        if not batches:
            return jsonify({'error': 'No batches found with the provided IDs'}), 404

        # Pause batches
        logger.info("4. Processing batches...")
        results = []
        for batch in batches:
            if batch.queue_position == 0:  # Only pause running batch
                logger.info(f"5. Pausing batch {batch.id}...")
                if queue_manager.state_manager.transition_state(batch, 'paused', None):
                    results.append(batch.to_dict())

        # Schedule queue update in background
        logger.info("6. Scheduling queue update...")
        queue_manager.schedule_queue_update()
        logger.info("7. Batch pause process complete")
        
        return jsonify(results)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error pausing batches: {str(e)}")
        return jsonify({'error': 'Failed to pause batches', 'details': str(e)}), 500

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
            logger.info(f"6. Deleting batch {batch.id}...")
            db.session.delete(batch)

        db.session.commit()

        # Schedule queue update
        logger.info("7. Scheduling queue update...")
        queue_manager.schedule_queue_update()
        logger.info("8. Batch deletion complete")
        
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
