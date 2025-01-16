"""
Profile API Routes
Handles HTTP endpoints for profile management
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models.profile import Profile
from models.base import db

# Create blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/api/profiles', methods=['GET'])
def list_profiles():
    """Get list of profiles with optional filtering"""
    # Build base query
    stmt = select(Profile)
    
    # Apply filters
    if 'status' in request.args:
        stmt = stmt.where(Profile.status == request.args['status'])
    
    if 'niche_id' in request.args:
        stmt = stmt.where(Profile.niche_id == request.args['niche_id'])
        
    # Execute query
    profiles = db.session.execute(stmt).scalars().all()
    return jsonify([profile.to_dict() for profile in profiles])

@profile_bp.route('/api/profiles/<profile_id>', methods=['GET'])
def get_profile(profile_id):
    """Get single profile by ID"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify(profile.to_dict())

@profile_bp.route('/api/profiles', methods=['POST'])
def create_profile():
    """Create new profile"""
    data = request.get_json()
    
    # Validate required fields
    if 'username' not in data:
        return jsonify({'error': 'username is required'}), 400
    
    try:
        # Create profile
        profile = Profile(
            username=data['username'],
            url=data.get('url'),
            status=data.get('status', 'active'),
            niche_id=data.get('niche_id')
        )
        
        # Save to database
        db.session.add(profile)
        db.session.commit()
        
        return jsonify(profile.to_dict()), 201
        
    except IntegrityError as e:
        db.session.rollback()
        if 'empty' in str(e):
            return jsonify({'error': 'Username cannot be empty'}), 400
        else:
            return jsonify({'error': 'Username already exists'}), 400
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@profile_bp.route('/api/profiles/bulk', methods=['POST'])
def bulk_create_profiles():
    """Bulk create profiles"""
    data = request.get_json()
    
    if 'profiles' not in data:
        return jsonify({'error': 'profiles array is required'}), 400
    
    created = []
    errors = []
    
    for profile_data in data['profiles']:
        try:
            # Create profile
            profile = Profile(
                username=profile_data['username'],
                url=profile_data.get('url'),
                status=profile_data.get('status', 'active'),
                niche_id=profile_data.get('niche_id')
            )
            
            # Save to database
            db.session.add(profile)
            db.session.commit()
            
            created.append(profile.to_dict())
            
        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            errors.append({
                'username': profile_data.get('username'),
                'error': str(e)
            })
    
    # Return 207 if partial success, 201 if all successful
    status_code = 207 if errors else 201
    return jsonify({
        'created': created,
        'errors': errors
    }), status_code

@profile_bp.route('/api/profiles/<profile_id>', methods=['PUT'])
def update_profile(profile_id):
    """Update existing profile"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update fields
        if 'username' in data:
            profile.username = data['username']
        if 'url' in data:
            profile.url = data['url']
        if 'status' in data:
            profile.set_status(data['status'])
        if 'niche_id' in data:
            profile.niche_id = data['niche_id']
            
        db.session.commit()
        return jsonify(profile.to_dict())
        
    except IntegrityError as e:
        db.session.rollback()
        if 'empty' in str(e):
            return jsonify({'error': 'Username cannot be empty'}), 400
        else:
            return jsonify({'error': 'Username already exists'}), 400
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@profile_bp.route('/api/profiles/<profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    """Soft delete profile"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    profile.soft_delete()
    db.session.commit()
    
    return '', 204

@profile_bp.route('/api/profiles/<profile_id>/reactivate', methods=['POST'])
def reactivate_profile(profile_id):
    """Reactivate soft-deleted profile"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    profile.reactivate()
    db.session.commit()
    
    return jsonify(profile.to_dict())

@profile_bp.route('/api/profiles/<profile_id>/record_check', methods=['POST'])
def record_check(profile_id):
    """Record story check result"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    data = request.get_json()
    story_detected = data.get('story_detected', False)
    
    profile.record_check(story_detected)
    db.session.commit()
    
    return jsonify(profile.to_dict())
