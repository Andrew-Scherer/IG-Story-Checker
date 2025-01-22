"""
Profile API Routes
Handles HTTP endpoints for profile management
"""

import re
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models.profile import Profile
from extensions import db
from utils.refresh_stories import refresh_stories


# Create blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('', methods=['GET'])
def list_profiles():
    """Get list of profiles with optional filtering"""
    try:
        current_app.logger.debug("Building profile query")
        stmt = select(Profile)
        
        if 'status' in request.args:
            status = request.args['status']
            current_app.logger.debug(f"Filtering by status: {status}")
            stmt = stmt.where(Profile.status == status)
        
        if 'niche_id' in request.args:
            niche_id = request.args['niche_id']
            current_app.logger.debug(f"Filtering by niche_id: {niche_id}")
            stmt = stmt.where(Profile.niche_id == niche_id)
            
        current_app.logger.debug("Executing profile query")
        profiles = db.session.execute(stmt).scalars().all()
        result = [profile.to_dict() for profile in profiles]
        current_app.logger.debug(f"Found {len(result)} profiles")
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error listing profiles: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/<profile_id>', methods=['GET'])
def get_profile(profile_id):
    """Get single profile by ID"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify(profile.to_dict())

@profile_bp.route('', methods=['POST'])
def create_profile():
    """Create new profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if 'username' not in data:
            return jsonify({'error': 'username is required'}), 400
            
        username = data['username']
        url = f"https://instagram.com/{username}"
        profile = Profile(
            username=username,
            url=url,
            status='active',
            niche_id=data.get('niche_id')
        )
        
        db.session.add(profile)
        db.session.commit()
        
        return jsonify(profile.to_dict()), 201
        
    except IntegrityError as e:
        db.session.rollback()
        if 'empty' in str(e):
            return jsonify({'error': 'Username cannot be empty'}), 400
        else:
            return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/niches/<niche_id>/import', methods=['POST'])
def import_profiles(niche_id):
    """Import profiles from file for a specific niche"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
            
        content = file.read().decode('utf-8')
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        created_profiles = []
        errors = []
        
        for line in lines:
            try:
                match = re.match(r'(?:https?:\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)\/([a-zA-Z0-9._]{1,30})(?:\/|\?|$)', line)
                username = match.group(1) if match else line
                
                if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
                    errors.append({
                        'line': line,
                        'error': 'Invalid username format'
                    })
                    continue
                
                existing = db.session.execute(
                    select(Profile).where(Profile.username == username)
                ).scalar()
                
                if existing:
                    errors.append({
                        'line': line,
                        'error': 'Profile already exists'
                    })
                    continue
                
                profile = Profile(
                    username=username,
                    url=f"https://instagram.com/{username}",
                    status='active',
                    niche_id=niche_id
                )
                
                db.session.add(profile)
                db.session.flush()
                created_profiles.append(profile.to_dict())
                
            except Exception as e:
                errors.append({
                    'line': line,
                    'error': str(e)
                })
                continue
        
        if created_profiles:
            db.session.commit()
            
        status_code = 207 if errors else 201
        return jsonify({
            'created': created_profiles,
            'errors': errors
        }), status_code
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/<profile_id>', methods=['PUT'])
def update_profile(profile_id):
    """Update existing profile"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    data = request.get_json()
    
    try:
        if 'username' in data:
            profile.username = data['username']
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

@profile_bp.route('/<profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    """Soft delete profile"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    profile.soft_delete()
    db.session.commit()
    
    return '', 204

@profile_bp.route('/<profile_id>/reactivate', methods=['POST'])
def reactivate_profile(profile_id):
    """Reactivate soft-deleted profile"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    profile.reactivate()
    db.session.commit()
    
    return jsonify(profile.to_dict())

@profile_bp.route('/refresh-stories', methods=['POST'])
def trigger_refresh_stories():
    """Trigger story status refresh"""
    try:
        refresh_stories()
        return jsonify({'message': 'Stories refreshed successfully'})
    except Exception as e:
        current_app.logger.error(f"Error refreshing stories: {str(e)}")
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/<profile_id>/record_check', methods=['POST'])
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
