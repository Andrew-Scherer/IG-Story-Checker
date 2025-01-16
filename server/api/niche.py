"""
Niche API Routes
Handles HTTP endpoints for niche management
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from models.niche import Niche
from models.base import db

# Create blueprint
niche_bp = Blueprint('niche', __name__)

@niche_bp.route('/api/niches', methods=['GET'])
def list_niches():
    """Get list of niches in display order"""
    niches = Niche.get_ordered()
    return jsonify([niche.to_dict() for niche in niches])

@niche_bp.route('/api/niches/<niche_id>', methods=['GET'])
def get_niche(niche_id):
    """Get single niche by ID"""
    niche = db.session.get(Niche, niche_id)
    if not niche:
        return jsonify({'error': 'Niche not found'}), 404
    
    return jsonify(niche.to_dict())

@niche_bp.route('/api/niches', methods=['POST'])
def create_niche():
    """Create new niche"""
    data = request.get_json()
    
    # Validate required fields
    if 'name' not in data:
        return jsonify({'error': 'name is required'}), 400
    
    try:
        # Create niche
        niche = Niche(
            name=data['name'],
            display_order=data.get('display_order')
        )
        
        # Save to database
        db.session.add(niche)
        db.session.commit()
        
        return jsonify(niche.to_dict()), 201
        
    except IntegrityError as e:
        db.session.rollback()
        if 'empty' in str(e):
            return jsonify({'error': 'Niche name cannot be empty'}), 400
        else:
            return jsonify({'error': 'Niche already exists'}), 400

@niche_bp.route('/api/niches/<niche_id>', methods=['PUT'])
def update_niche(niche_id):
    """Update existing niche"""
    niche = db.session.get(Niche, niche_id)
    if not niche:
        return jsonify({'error': 'Niche not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update fields
        if 'name' in data:
            if not data['name'] or not data['name'].strip():
                return jsonify({'error': 'Niche name cannot be empty'}), 400
            niche.name = data['name']
        if 'display_order' in data:
            niche.display_order = data['display_order']
            
        db.session.commit()
        return jsonify(niche.to_dict())
        
    except IntegrityError as e:
        db.session.rollback()
        if 'empty' in str(e):
            return jsonify({'error': 'Niche name cannot be empty'}), 400
        else:
            return jsonify({'error': 'Niche already exists'}), 400

@niche_bp.route('/api/niches/<niche_id>', methods=['DELETE'])
def delete_niche(niche_id):
    """Delete niche"""
    niche = db.session.get(Niche, niche_id)
    if not niche:
        return jsonify({'error': 'Niche not found'}), 404
    
    db.session.delete(niche)
    db.session.commit()
    
    return '', 204

@niche_bp.route('/api/niches/reorder', methods=['POST'])
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
