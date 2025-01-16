"""
Niche API Resources
Handles niche management endpoints
"""

from flask import request
from flask_restful import Resource, reqparse, fields, marshal_with, abort
from models import db, Niche, Profile, StoryResult
from datetime import datetime

# Response fields
niche_fields = {
    'id': fields.String,
    'name': fields.String,
    'description': fields.String,
    'order': fields.Integer,
    'daily_story_target': fields.Integer,
    'total_profiles': fields.Integer,
    'active_profiles': fields.Integer,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601')
}

# Request parsers
niche_parser = reqparse.RequestParser()
niche_parser.add_argument('name', type=str, required=True, help='Niche name is required')
niche_parser.add_argument('description', type=str)
niche_parser.add_argument('daily_story_target', type=int, default=20)

reorder_parser = reqparse.RequestParser()
reorder_parser.add_argument('order', type=list, required=True, location='json',
                           help='List of niche IDs in desired order')

class NicheListResource(Resource):
    """Resource for managing niche collections"""
    
    @marshal_with(niche_fields)
    def get(self):
        """Get all niches in display order"""
        return Niche.query.order_by(Niche.order).all()

    @marshal_with(niche_fields)
    def post(self):
        """Create new niche"""
        args = niche_parser.parse_args()
        
        # Check for duplicate name
        if Niche.query.filter_by(name=args['name']).first():
            abort(400, message=f"Niche with name '{args['name']}' already exists")
        
        # Create niche
        niche = Niche(
            name=args['name'],
            description=args.get('description'),
            daily_story_target=args['daily_story_target']
        )
        niche.save()
        
        return niche, 201

class NicheResource(Resource):
    """Resource for managing individual niches"""
    
    @marshal_with(niche_fields)
    def get(self, niche_id):
        """Get specific niche"""
        niche = Niche.get_by_id(niche_id)
        if not niche:
            abort(404, message=f"Niche {niche_id} not found")
        return niche

    @marshal_with(niche_fields)
    def put(self, niche_id):
        """Update specific niche"""
        niche = Niche.get_by_id(niche_id)
        if not niche:
            abort(404, message=f"Niche {niche_id} not found")
        
        args = niche_parser.parse_args()
        
        # Check for duplicate name if changing
        if args['name'] != niche.name:
            existing = Niche.query.filter_by(name=args['name']).first()
            if existing:
                abort(400, message=f"Niche with name '{args['name']}' already exists")
        
        # Update fields
        niche.name = args['name']
        niche.description = args.get('description')
        niche.daily_story_target = args['daily_story_target']
        niche.save()
        
        return niche

    def delete(self, niche_id):
        """Delete specific niche"""
        niche = Niche.get_by_id(niche_id)
        if not niche:
            abort(404, message=f"Niche {niche_id} not found")
        
        # Update profiles to remove niche
        Profile.query.filter_by(niche_id=niche_id).update({'niche_id': None})
        
        niche.delete()
        return '', 204

    def get_profiles(self, niche_id):
        """Get profiles for specific niche"""
        niche = Niche.get_by_id(niche_id)
        if not niche:
            abort(404, message=f"Niche {niche_id} not found")
        
        profiles = Profile.query.filter_by(niche_id=niche_id).all()
        return [p.to_dict() for p in profiles]

    def get_stats(self, niche_id):
        """Get statistics for specific niche"""
        niche = Niche.get_by_id(niche_id)
        if not niche:
            abort(404, message=f"Niche {niche_id} not found")
        
        # Get current story count
        current_stories = StoryResult.query.join(
            Profile, StoryResult.profile_id == Profile.id
        ).filter(
            Profile.niche_id == niche_id,
            StoryResult.expires_at > datetime.utcnow()
        ).count()
        
        return {
            'total_profiles': niche.total_profiles,
            'active_profiles': niche.active_profiles,
            'current_stories': current_stories
        }

class NicheReorderResource(Resource):
    """Resource for reordering niches"""
    
    @marshal_with(niche_fields)
    def post(self):
        """Reorder niches"""
        args = reorder_parser.parse_args()
        niche_ids = args['order']
        
        # Verify all niches exist
        niches = Niche.query.filter(Niche.id.in_(niche_ids)).all()
        if len(niches) != len(niche_ids):
            abort(400, message="Invalid niche IDs in order list")
        
        # Update order
        Niche.reorder(niche_ids)
        
        return Niche.query.order_by(Niche.order).all()
