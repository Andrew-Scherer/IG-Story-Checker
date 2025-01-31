"""
Profile API Routes
Handles HTTP endpoints for profile management
"""

import re
import traceback
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from models.profile import Profile
from models.niche import Niche
from extensions import db
from utils.refresh_stories import refresh_stories
from utils.query_builder import ProfileQueryBuilder

# Create blueprint
profile_bp = Blueprint('profile', __name__)

# Valid sort columns and their descriptions
VALID_SORT_COLUMNS = {
    'username': 'Profile username',
    'niche__name': 'Niche name',
    'status': 'Profile status',
    'last_checked': 'Last check timestamp',
    'last_detected': 'Last story detection timestamp',
    'detection_rate': 'Story detection rate (total_detections/total_checks)',
    'total_detections': 'Total story detections',
    'total_checks': 'Total profile checks',
    'active_story': 'Has active story',
    'created_at': 'Profile creation timestamp',
    'updated_at': 'Profile last update timestamp'
}

def validate_sort_params(sort_by: str, sort_direction: str) -> tuple[str, str]:
    """Validate and normalize sort parameters"""
    if sort_by and sort_by not in VALID_SORT_COLUMNS:
        raise ValueError(
            f"Invalid sort column: {sort_by}. Valid columns are: {', '.join(VALID_SORT_COLUMNS.keys())}"
        )
    
    if sort_direction and sort_direction not in ('asc', 'desc'):
        raise ValueError("Sort direction must be 'asc' or 'desc'")
        
    return sort_by, sort_direction.lower() if sort_direction else 'asc'

@profile_bp.route('', methods=['GET'])
def list_profiles():
    """Get list of profiles with optional filtering, sorting, and pagination"""
    try:
        current_app.logger.debug("Building profile query")
        query_builder = ProfileQueryBuilder(Profile)
        
        # Add filters
        if 'status' in request.args:
            status = request.args['status']
            current_app.logger.debug(f"Filtering by status: {status}")
            query_builder.with_status(status)
        
        if 'niche_id' in request.args:
            niche_id = request.args['niche_id']
            current_app.logger.info(f"Filtering by niche_id: {niche_id}")
            query_builder.with_niche_id(niche_id)

        if 'search' in request.args:
            search = request.args['search']
            current_app.logger.info(f"Filtering by search: {search}")
            query_builder.with_search(search)
        
        # Validate and add sorting
        try:
            sort_column, sort_direction = validate_sort_params(
                request.args.get('sort_by'),
                request.args.get('sort_direction')
            )
            current_app.logger.debug(f"Sorting by {sort_column} {sort_direction}")
            query_builder.with_sorting(sort_column, sort_direction)
        except ValueError as e:
            current_app.logger.warning(f"Sort validation failed: {str(e)}")
            return jsonify({'error': str(e)}), 400
        
        # Add pagination
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        current_app.logger.debug(f"Paginating: page={page}, page_size={page_size}")
        query_builder.with_pagination(page, page_size)
        
        # Build and execute main query
        current_app.logger.info("=== Executing Profile Query ===")
        main_query = query_builder.build()
        current_app.logger.info(f"Final SQL Query: {main_query}")
        
        profiles = db.session.execute(main_query).scalars().all()
        current_app.logger.info(f"Raw Query Results: {profiles}")
        
        result = [profile.to_dict() for profile in profiles]
        current_app.logger.info(f"Processed Results Count: {len(result)}")
        if result:
            current_app.logger.info(f"Sample Result: {result[0]}")
        
        # Get total count using the same filters
        count_query = query_builder.build_count()
        current_app.logger.info(f"Count Query: {count_query}")
        total_count = db.session.execute(count_query).scalar()
        current_app.logger.info(f"Total Count Result: {total_count}")
        
        response_data = {
            'profiles': result,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'sort_column': sort_column,
            'sort_direction': sort_direction,
            'filters': {
                'search': request.args.get('search'),
                'niche_id': request.args.get('niche_id'),
                'status': request.args.get('status')
            }
        }
        
        current_app.logger.info(f"Returning response with filters: {response_data['filters']}")
        return jsonify(response_data)
        
    except ValueError as e:
        current_app.logger.error(f"Invalid parameter value: {str(e)}")
        return jsonify({'error': f"Invalid parameter value: {str(e)}"}), 400
    except Exception as e:
        current_app.logger.error(f"Error listing profiles: {str(e)}")
        current_app.logger.exception("Exception details:")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/<profile_id>', methods=['GET'])
def get_profile(profile_id):
    """Get single profile by ID"""
    profile = db.session.get(Profile, profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify(profile.to_dict())

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
        
        current_app.logger.info(f"Starting import of {len(lines)} profiles for niche {niche_id}")
        
        # Validate niche_id
        niche = db.session.execute(
            select(Niche).where(Niche.id == niche_id)
        ).scalar()
        if not niche:
            current_app.logger.error(f"Invalid niche_id: {niche_id} - Niche not found")
            return jsonify({'error': f'Invalid niche_id: {niche_id}'}), 400
        current_app.logger.info(f"Using niche '{niche.name}' (ID: {niche_id})")
        
        created_profiles = []
        errors = []
        duplicate_count = 0
        invalid_format_count = 0
        
        for index, line in enumerate(lines, start=1):
            try:
                match = re.match(r'(?:https?:\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)\/([a-zA-Z0-9._]{1,30})(?:\/|\?|$)', line)
                username = match.group(1) if match else line
                
                if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
                    errors.append({
                        'line': line,
                        'error': 'Invalid username format'
                    })
                    invalid_format_count += 1
                    current_app.logger.debug(f"Invalid username format: {username}")
                    continue

                # First validate niche_id exists
                current_app.logger.info(f"Processing profile import - Username: {username}, Niche ID: {niche_id}")
                
                # Validate niche exists (we already validated at the start, but check again in case it was deleted)
                current_app.logger.debug(f"Validating niche_id: {niche_id}")
                niche = db.session.execute(
                    select(Niche).where(Niche.id == niche_id)
                ).scalar()
                
                if not niche:
                    error_msg = f"Invalid niche_id: {niche_id} - Niche not found"
                    current_app.logger.error(error_msg)
                    errors.append({
                        'line': line,
                        'error': error_msg
                    })
                    continue
                    
                current_app.logger.info(f"Found niche: {niche.name} (ID: {niche.id})")
                
                # Then check for duplicates
                normalized_username = username.lower().replace('.', '_')
                current_app.logger.debug(f"Normalized username: {normalized_username} (original: {username})")
                
                existing = db.session.execute(
                    select(Profile).where(
                        func.lower(Profile.username).replace('.', '_') == normalized_username
                    )
                ).scalar()
                
                if existing:
                    errors.append({
                        'line': line,
                        'error': f'Profile already exists (as {existing.username})'
                    })
                    duplicate_count += 1
                    current_app.logger.debug(f"Duplicate profile detected: {username} matches existing {existing.username}")
                    continue
                
                # Create profile with the validated niche
                current_app.logger.info(f"Creating profile '{username}' with niche_id: {niche_id}")
                
                profile = Profile(
                    username=username,
                    url=f"https://instagram.com/{username}",
                    status='active',
                    niche_id=niche_id
                )
                
                current_app.logger.debug(f"Profile object created: {profile.__dict__}")
                
                # Add to session and verify niche assignment
                db.session.add(profile)
                db.session.flush()  # Flush to get the ID assigned
                
                # Verify niche assignment after flush
                if profile.niche_id != niche_id:
                    error_msg = (
                        f"Niche assignment failed for profile '{username}': "
                        f"expected {niche_id}, got {profile.niche_id}"
                    )
                    current_app.logger.error(error_msg)
                    errors.append({
                        'line': line,
                        'error': error_msg
                    })
                    continue
                
                current_app.logger.info(
                    f"Profile '{username}' (ID: {profile.id}) created with "
                    f"niche_id: {profile.niche_id}"
                )
                
                created_profiles.append(profile.to_dict())
                
                if index % 100 == 0:
                    current_app.logger.info(f"Processed {index} profiles. Created: {len(created_profiles)}, Errors: {len(errors)}")
                    db.session.commit()  # Commit in batches
                
            except Exception as e:
                current_app.logger.error(f"Error processing profile {line}: {str(e)}")
                current_app.logger.exception("Exception details:")
                errors.append({
                    'line': line,
                    'error': str(e)
                })
                continue
        
        if created_profiles:
            # Final verification of all created profiles
            current_app.logger.info("Performing final verification of all created profiles...")
            
            for profile_dict in created_profiles:
                profile = db.session.execute(
                    select(Profile).where(Profile.id == profile_dict['id'])
                ).scalar()
                
                if not profile:
                    error_msg = f"Profile {profile_dict['id']} not found in database"
                    current_app.logger.error(error_msg)
                    db.session.rollback()
                    return jsonify({'error': error_msg}), 500
                
                if profile.niche_id != profile_dict['niche_id']:
                    error_msg = (
                        f"Niche mismatch for profile '{profile.username}': "
                        f"expected {profile_dict['niche_id']}, got {profile.niche_id}"
                    )
                    current_app.logger.error(error_msg)
                    db.session.rollback()
                    return jsonify({'error': error_msg}), 500
            
            current_app.logger.info("All profile verifications passed, committing transaction...")
            db.session.commit()
            
        current_app.logger.info(
            f"Import completed successfully. "
            f"Total profiles: {len(lines)}, "
            f"Created: {len(created_profiles)}, "
            f"Errors: {len(errors)}, "
            f"Duplicates: {duplicate_count}, "
            f"Invalid format: {invalid_format_count}"
        )
        
        status_code = 207 if errors else 201
        return jsonify({
            'created': created_profiles,
            'errors': errors,
            'total': len(lines),
            'created_count': len(created_profiles),
            'error_count': len(errors),
            'duplicate_count': duplicate_count,
            'invalid_format_count': invalid_format_count
        }), status_code
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during profile import: {str(e)}")
        current_app.logger.exception("Exception details:")
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/refresh-stories', methods=['POST'])
def trigger_refresh_stories():
    """Trigger story status refresh"""
    try:
        refresh_stories()
        return jsonify({'message': 'Stories refreshed successfully'})
    except Exception as e:
        current_app.logger.error(f"Error refreshing stories: {str(e)}")
        current_app.logger.exception("Exception details:")
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
