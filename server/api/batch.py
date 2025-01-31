"""
Batch API Routes
Handles batch operations endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from models import db, Batch, BatchLog
from services.batch_manager import BatchManager

batch_bp = Blueprint('batch', __name__, url_prefix='/batches')
batch_manager = BatchManager(db.session)

@batch_bp.route('/<batch_id>/logs', methods=['GET'])
def get_batch_logs(batch_id):
    """Get logs for a specific batch"""
    try:
        # Get pagination params
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get total count first
        total = BatchLog.query\
            .filter(BatchLog.batch_id == batch_id)\
            .count()

        # Then get paginated logs
        logs = BatchLog.query\
            .filter(BatchLog.batch_id == batch_id)\
            .order_by(BatchLog.timestamp.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
            
        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'total': total
        })
    except Exception as e:
        current_app.logger.error(f"Error getting batch logs: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@batch_bp.route('/start', methods=['POST'])
def start_batches():
    """Start selected batches"""
    try:
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        results = []
        for batch_id in data['batch_ids']:
            if batch_manager.start_batch(batch_id):
                db.session.commit()  # Commit changes immediately
                # Get fresh instance after commit
                batch = db.session.get(Batch, batch_id)
                if batch:
                    results.append(batch.to_dict())

        return jsonify(results)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error starting batches: {str(e)}")
        return jsonify({'error': 'Failed to start batches'}), 500


@batch_bp.route('', methods=['GET'])
def list_batches():
    """List all batches"""
    try:
        batches = Batch.query.all()
        return jsonify([batch.to_dict() for batch in batches])
    except Exception as e:
        current_app.logger.error(f"Error listing batches: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@batch_bp.route('', methods=['POST'])
def create_batch():
    """Create new batch from selected profiles"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        if not data.get('niche_id'):
            return jsonify({'error': 'niche_id is required'}), 400

        profile_ids = data.get('profile_ids')
        if not profile_ids:
            return jsonify({'error': 'profile_ids is required'}), 400

        # Create batch
        batch = Batch(niche_id=data['niche_id'], profile_ids=profile_ids)
        db.session.add(batch)
        db.session.flush()  # Get batch ID

        # Queue the batch and commit
        if batch_manager.queue_batch(batch.id):
            db.session.commit()
            # Get fresh instance after commit
            batch = db.session.get(Batch, batch.id)
            return jsonify(batch.to_dict()), 201
        else:
            db.session.rollback()
            return jsonify({'error': 'Failed to queue batch'}), 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating batch: {str(e)}")
        return jsonify({'error': 'Failed to create batch'}), 500

@batch_bp.route('/resume', methods=['POST'])
def resume_batches():
    """Resume paused batches"""
    try:
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        results = []
        for batch_id in data['batch_ids']:
            if batch_manager.queue_batch(batch_id):
                db.session.commit()  # Commit changes immediately
                # Get fresh instance after commit
                batch = db.session.get(Batch, batch_id)
                if batch:
                    results.append(batch.to_dict())

        return jsonify(results)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resuming batches: {str(e)}")
        return jsonify({'error': 'Failed to resume batches'}), 500

@batch_bp.route('/stop', methods=['POST'])
def stop_batches():
    """Stop selected batches"""
    try:
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        results = []
        for batch_id in data['batch_ids']:
            if batch_manager.pause_batch(batch_id):
                db.session.commit()  # Commit changes immediately
                # Get fresh instance after commit
                batch = db.session.get(Batch, batch_id)
                if batch:
                    results.append(batch.to_dict())

        return jsonify(results)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error stopping batches: {str(e)}")
        return jsonify({'error': 'Failed to stop batches'}), 500

@batch_bp.route('/refresh', methods=['POST'])
def refresh_batches():
    """Refresh selected batches"""
    try:
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        results = []
        for batch_id in data['batch_ids']:
            if batch_manager.queue_batch(batch_id):
                db.session.commit()  # Commit changes immediately
                # Get fresh instance after commit
                batch = db.session.get(Batch, batch_id)
                if batch:
                    results.append(batch.to_dict())

        return jsonify(results)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error refreshing batches: {str(e)}")
        return jsonify({'error': 'Failed to refresh batches'}), 500

@batch_bp.route('', methods=['DELETE'])
def delete_batches():
    """Delete selected batches"""
    try:
        data = request.get_json()
        if not data or not data.get('batch_ids'):
            return jsonify({'error': 'batch_ids is required'}), 400

        for batch_id in data['batch_ids']:
            batch = db.session.get(Batch, batch_id)
            if batch:
                batch_manager.pause_batch(batch_id)  # Stop if running
                db.session.delete(batch)

        db.session.commit()
        return '', 204

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting batches: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
