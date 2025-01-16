"""
Batch API Routes
Handles batch processing endpoints
"""

from datetime import datetime, timedelta, UTC
from flask import Blueprint, request, jsonify
from sqlalchemy import and_, or_
from models import db, Batch, BatchProfile, Profile, Niche, StoryResult, SystemSettings

# Create blueprint
batch_bp = Blueprint('batch', __name__)

@batch_bp.route('/api/batches', methods=['GET'])
def list_batches():
    """Get batches with optional filtering"""
    # Apply filters
    query = Batch.query
    
    if request.args.get('status') == 'active':
        query = query.filter(Batch.status.in_(['pending', 'running']))
    elif request.args.get('status'):
        query = query.filter_by(status=request.args['status'])
    
    if request.args.get('niche_id'):
        query = query.filter_by(niche_id=request.args['niche_id'])
    
    batches = query.order_by(Batch.created_at.desc()).all()
    return jsonify([batch.to_dict() for batch in batches])

@batch_bp.route('/api/batches', methods=['POST'])
def create_batch():
    """Create new batch"""
    data = request.get_json()
    
    # Validate required fields
    if 'niche_id' not in data:
        return jsonify({'message': 'niche_id is required'}), 400
    
    # Validate niche
    niche = db.session.get(Niche, data['niche_id'])
    if not niche:
        return jsonify({'message': f"Invalid niche ID: {data['niche_id']}"}), 400
    
    # Check for existing active batch
    active_batch = db.session.execute(
        db.select(Batch).filter(
            Batch.niche_id == data['niche_id'],
            Batch.status.in_(['pending', 'running'])
        )
    ).scalar_one_or_none()
    if active_batch:
        return jsonify({'message': f"Batch already in progress for niche {data['niche_id']}"}), 400
    
    # Get profiles for batch
    profile_count = data.get('profile_count', 100)
    profiles = db.session.execute(
        db.select(Profile)
        .filter(
            Profile.niche_id == data['niche_id'],
            Profile.status == 'active'
        )
        .order_by(Profile.last_checked.asc().nullsfirst())
        .limit(profile_count)
    ).scalars().all()
    
    if not profiles:
        return jsonify({'message': f"No profiles available for niche {data['niche_id']}"}), 400
    
    # Create and commit batch first
    batch = Batch(niche_id=data['niche_id'])
    db.session.add(batch)
    db.session.commit()
    
    # Now add profiles to the committed batch
    for profile in profiles:
        batch_profile = BatchProfile(batch_id=batch.id, profile_id=profile.id)
        db.session.add(batch_profile)
    
    db.session.commit()
    batch.update_stats(db.session)
    
    return jsonify(batch.to_dict()), 201

@batch_bp.route('/api/batches/<batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get specific batch"""
    batch = Batch.get_by_id(batch_id)
    if not batch:
        return jsonify({'message': f"Batch {batch_id} not found"}), 404
    
    return jsonify(batch.to_dict())

@batch_bp.route('/api/batches/<batch_id>/cancel', methods=['POST'])
def cancel_batch(batch_id):
    """Cancel batch"""
    batch = Batch.get_by_id(batch_id)
    if not batch:
        return jsonify({'message': f"Batch {batch_id} not found"}), 404
    
    if batch.status not in ['pending', 'running']:
        return jsonify({'message': f"Cannot cancel batch in {batch.status} status"}), 400
    
    batch.status = 'cancelled'
    batch.end_time = datetime.now(UTC)
    db.session.commit()
    
    return jsonify(batch.to_dict())

@batch_bp.route('/api/batches/<batch_id>/results', methods=['GET'])
def get_batch_results(batch_id):
    """Get story results for batch"""
    batch = Batch.get_by_id(batch_id)
    if not batch:
        return jsonify({'message': f"Batch {batch_id} not found"}), 404
    
    results = db.session.execute(
        db.select(StoryResult).filter_by(batch_id=batch_id)
    ).scalars().all()
    return jsonify([result.to_dict() for result in results])

@batch_bp.route('/api/batches/<batch_id>/progress', methods=['GET'])
def get_batch_progress(batch_id):
    """Get batch progress details"""
    batch = Batch.get_by_id(batch_id)
    if not batch:
        return jsonify({'message': f"Batch {batch_id} not found"}), 404
    
    stats = db.session.query(
        db.func.count(BatchProfile.id).label('total'),
        db.func.sum(
            db.case((BatchProfile.status == 'completed', 1), else_=0)
        ).label('completed'),
        db.func.sum(
            db.case((BatchProfile.has_story == True, 1), else_=0)
        ).label('successful'),
        db.func.sum(
            db.case((BatchProfile.status == 'pending', 1), else_=0)
        ).label('pending')
    ).filter(BatchProfile.batch_id == batch_id).first()
    
    return jsonify({
        'total_profiles': stats.total or 0,
        'completed_profiles': stats.completed or 0,
        'successful_checks': stats.successful or 0,
        'pending_profiles': stats.pending or 0
    })

@batch_bp.route('/api/batches/auto-trigger', methods=['POST'])
def auto_trigger_batches():
    """Auto-trigger batches for niches below target"""
    settings = SystemSettings.get_settings()
    if not settings.auto_trigger_enabled:
        return jsonify({'triggered': []})
    
    triggered = []
    niches = db.session.execute(db.select(Niche)).scalars().all()
    for niche in niches:
        # Skip if active batch exists
        active_batch = db.session.execute(
            db.select(Batch).filter(
                Batch.niche_id == niche.id,
                Batch.status.in_(['pending', 'running'])
            )
        ).scalar_one_or_none()
        if active_batch:
            continue
        
        # Check current story count
        current_stories = db.session.execute(
            db.select(db.func.count())
            .select_from(StoryResult)
            .join(Profile, StoryResult.profile_id == Profile.id)
            .filter(
                Profile.niche_id == niche.id,
                StoryResult.expires_at > datetime.now(UTC)
            )
        ).scalar_one()
        
        # Trigger batch if below target
        if current_stories < niche.daily_story_target:
            batch = Batch(niche_id=niche.id)
            db.session.add(batch)
            
            # Add profiles
            profiles = db.session.execute(
                db.select(Profile)
                .filter(
                    Profile.niche_id == niche.id,
                    Profile.status == 'active'
                )
                .order_by(Profile.last_checked.asc().nullsfirst())
                .limit(settings.default_batch_size)
            ).scalars().all()
            
            for profile in profiles:
                batch_profile = BatchProfile(batch_id=batch.id, profile_id=profile.id)
                db.session.add(batch_profile)
            
            db.session.commit()
            batch.update_stats()
            triggered.append(batch.to_dict())
    
    return jsonify({'triggered': triggered})

@batch_bp.route('/api/batches/cleanup', methods=['POST'])
def cleanup_batches():
    """Clean up old completed batches"""
    cutoff = datetime.now(UTC) - timedelta(days=7)
    
    # First get all completed batches
    completed_batches = db.session.execute(
        db.select(Batch).where(Batch.status == 'completed')
    ).scalars().all()
    
    # Filter old batches in Python where we can safely compare timezone-aware datetimes
    old_batches = [b for b in completed_batches if b.end_time and b.end_time < cutoff]
    count = len(old_batches)
    
    if count > 0:
        # Delete associated batch profiles
        batch_ids = [b.id for b in old_batches]
        db.session.execute(
            db.delete(BatchProfile).where(BatchProfile.batch_id.in_(batch_ids))
        )
        
        # Delete the batches
        for batch in old_batches:
            db.session.delete(batch)
        
        db.session.commit()
    
    return jsonify({'cleaned': count})
