"""
Niche API Routes
Handles HTTP endpoints for niche management
"""

import traceback
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from models.niche import Niche
from extensions import db
from reassign_profiles_to_first_niche import reassign_profiles

# Create blueprint
niche_bp = Blueprint('niche', __name__)

@niche_bp.route('', methods=['GET'])
def list_niches():
    """Get list of niches in display order"""
    try:
        current_app.logger.info("=== GET /api/niches ===")
        current_app.logger.info("1. Fetching ordered niches...")
        niches = Niche.get_ordered()
        current_app.logger.info(f"2. Found {len(niches) if niches else 0} niches")
        
        current_app.logger.info("3. Converting niches to dict...")
        result = [niche.to_dict() for niche in niches]
        current_app.logger.info("4. Successfully converted niches")
        current_app.logger.info(f"Niche details: {result}")
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error("!!! Error in list_niches !!!")
        current_app.logger.error(f"Error type: {type(e).__name__}")
        current_app.logger.error(f"Error message: {str(e)}")
        current_app.logger.error("Full traceback:", exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

@niche_bp.route('/<niche_id>', methods=['GET'])
def get_niche(niche_id):
    """Get single niche by ID"""
    niche = db.session.get(Niche, niche_id)
    if not niche:
        return jsonify({'error': 'Niche not found'}), 404
    
    return jsonify(niche.to_dict())

@niche_bp.route('', methods=['POST'])
def create_niche():
    """Create new niche"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if 'name' not in data:
            return jsonify({'error': 'name is required'}), 400
        
        niche = Niche(
            name=data['name'],
            order=data.get('order')
        )
        
        db.session.add(niche)
        db.session.commit()
        
        return jsonify(niche.to_dict()), 201
        
    except IntegrityError as e:
        db.session.rollback()
        if 'empty' in str(e):
            return jsonify({'error': 'Niche name cannot be empty'}), 400
        else:
            return jsonify({'error': 'Niche already exists'}), 400

@niche_bp.route('/<niche_id>', methods=['PUT'])
def update_niche(niche_id):
    """Update existing niche"""
    niche = db.session.get(Niche, niche_id)
    if not niche:
        return jsonify({'error': 'Niche not found'}), 404
    
    data = request.get_json()
    
    try:
        if 'name' in data:
            if not data['name'] or not data['name'].strip():
                return jsonify({'error': 'Niche name cannot be empty'}), 400
            niche.name = data['name']
        if 'order' in data:
            niche.order = data['order']
            
        db.session.commit()
        return jsonify(niche.to_dict())
        
    except IntegrityError as e:
        db.session.rollback()
        if 'empty' in str(e):
            return jsonify({'error': 'Niche name cannot be empty'}), 400
        else:
            return jsonify({'error': 'Niche already exists'}), 400

@niche_bp.route('/<niche_id>', methods=['DELETE'])
def delete_niche(niche_id):
    """Delete niche and reassign its profiles to the first available niche"""
    try:
        niche = db.session.get(Niche, niche_id)
        if not niche:
            return jsonify({'error': 'Niche not found'}), 404

        # First reassign profiles to the first available niche
        if not reassign_profiles(niche_id):
            return jsonify({'error': 'Failed to reassign profiles'}), 500

        # Then delete any batches associated with this niche
        from models.batch import Batch
        batches = Batch.query.filter_by(niche_id=niche_id).all()
        for batch in batches:
            db.session.delete(batch)
        
        # Finally delete the niche
        db.session.delete(niche)
        db.session.commit()
        
        return '', 204
        
    except Exception as e:
        current_app.logger.error(f"Error deleting niche: {str(e)}")
        current_app.logger.exception("Exception details:")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@niche_bp.route('/reorder', methods=['POST'])
def reorder_niches():
    """Reorder niches"""
    data = request.get_json()
    
    if 'niche_ids' not in data:
        return jsonify({'error': 'niche_ids is required'}), 400
    
    niche_ids = data['niche_ids']
    
    # Verify all niches exist
    existing_ids = {n.id for n in Niche.query.all()}
    if not all(nid in existing_ids for nid in niche_ids):
        return jsonify({'error': 'Invalid niche ID'}), 400
    
    # Verify all niches included
    if len(niche_ids) != len(existing_ids):
        return jsonify({'error': 'All niches must be included'}), 400
    
    # Update order
    Niche.reorder(niche_ids)
    db.session.commit()
    
    return jsonify({'message': 'Niches reordered successfully'})
