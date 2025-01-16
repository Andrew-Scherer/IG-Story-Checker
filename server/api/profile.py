"""
Profile API Resources
Handles profile management endpoints
"""

from flask import request
from flask_restful import Resource, reqparse, fields, marshal_with, abort
from sqlalchemy import or_
from models import db, Profile, Niche

# Response fields
profile_fields = {
    'id': fields.String,
    'username': fields.String,
    'url': fields.String,
    'niche_id': fields.String,
    'status': fields.String,
    'last_checked': fields.DateTime(dt_format='iso8601'),
    'last_detected': fields.DateTime(dt_format='iso8601'),
    'total_checks': fields.Integer,
    'total_detections': fields.Integer,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601')
}

# Request parsers
profile_parser = reqparse.RequestParser()
profile_parser.add_argument('username', type=str, required=True, help='Username is required')
profile_parser.add_argument('niche_id', type=str)
profile_parser.add_argument('status', type=str, choices=('active', 'deleted'))

bulk_parser = reqparse.RequestParser()
bulk_parser.add_argument('ids', type=list, required=True, location='json',
                        help='List of profile IDs required')
bulk_parser.add_argument('niche_id', type=str)

import_parser = reqparse.RequestParser()
import_parser.add_argument('usernames', type=list, required=True, location='json',
                          help='List of usernames required')
import_parser.add_argument('niche_id', type=str)

filter_parser = reqparse.RequestParser()
filter_parser.add_argument('niche_id', type=str)
filter_parser.add_argument('status', type=str)
filter_parser.add_argument('search', type=str)

class ProfileListResource(Resource):
    """Resource for managing profile collections"""
    
    @marshal_with(profile_fields)
    def get(self):
        """Get profiles with optional filtering"""
        args = filter_parser.parse_args()
        query = Profile.query
        
        if args.get('niche_id'):
            query = query.filter_by(niche_id=args['niche_id'])
        
        if args.get('status'):
            query = query.filter_by(status=args['status'])
        
        if args.get('search'):
            search = f"%{args['search']}%"
            query = query.filter(Profile.username.ilike(search))
        
        return query.all()

    @marshal_with(profile_fields)
    def post(self):
        """Create new profile"""
        args = profile_parser.parse_args()
        
        # Check for duplicate username
        if Profile.query.filter_by(username=args['username'].lower()).first():
            abort(400, message=f"Profile with username '{args['username']}' already exists")
        
        # Validate niche if provided
        if args.get('niche_id'):
            niche = Niche.get_by_id(args['niche_id'])
            if not niche:
                abort(400, message=f"Invalid niche ID: {args['niche_id']}")
        
        # Create profile
        profile = Profile(
            username=args['username'],
            niche_id=args.get('niche_id')
        )
        profile.save()
        
        return profile, 201

class ProfileResource(Resource):
    """Resource for managing individual profiles"""
    
    @marshal_with(profile_fields)
    def get(self, profile_id):
        """Get specific profile"""
        profile = Profile.get_by_id(profile_id)
        if not profile:
            abort(404, message=f"Profile {profile_id} not found")
        return profile

    @marshal_with(profile_fields)
    def put(self, profile_id):
        """Update specific profile"""
        profile = Profile.get_by_id(profile_id)
        if not profile:
            abort(404, message=f"Profile {profile_id} not found")
        
        args = profile_parser.parse_args()
        
        # Validate niche if changing
        if args.get('niche_id') and args['niche_id'] != profile.niche_id:
            niche = Niche.get_by_id(args['niche_id'])
            if not niche:
                abort(400, message=f"Invalid niche ID: {args['niche_id']}")
            profile.niche_id = args['niche_id']
        
        # Update status if provided
        if args.get('status'):
            profile.status = args['status']
        
        profile.save()
        return profile

    def delete(self, profile_id):
        """Delete specific profile"""
        profile = Profile.get_by_id(profile_id)
        if not profile:
            abort(404, message=f"Profile {profile_id} not found")
        
        profile.delete()
        return '', 204

class ProfileBulkResource(Resource):
    """Resource for bulk profile operations"""
    
    def post(self, action):
        """Handle bulk operations"""
        args = bulk_parser.parse_args()
        profile_ids = args['ids']
        
        if action == 'bulk-delete':
            # Delete multiple profiles
            deleted = Profile.query.filter(Profile.id.in_(profile_ids)).delete(
                synchronize_session=False
            )
            db.session.commit()
            
            return {'deleted': deleted}
        
        elif action == 'bulk-update':
            # Validate niche
            niche_id = args.get('niche_id')
            if niche_id:
                niche = Niche.get_by_id(niche_id)
                if not niche:
                    abort(400, message=f"Invalid niche ID: {niche_id}")
            
            # Update profiles
            updated = Profile.query.filter(Profile.id.in_(profile_ids)).update({
                'niche_id': niche_id
            }, synchronize_session=False)
            db.session.commit()
            
            return {'updated': updated}
        
        abort(400, message=f"Invalid bulk action: {action}")

class ProfileImportResource(Resource):
    """Resource for importing profiles"""
    
    def post(self):
        """Import profiles from username list"""
        args = import_parser.parse_args()
        usernames = [u.lower().strip() for u in args['usernames']]
        
        # Validate niche if provided
        niche_id = args.get('niche_id')
        if niche_id:
            niche = Niche.get_by_id(niche_id)
            if not niche:
                abort(400, message=f"Invalid niche ID: {niche_id}")
        
        # Find existing usernames
        existing = set(p.username for p in Profile.query.filter(
            Profile.username.in_(usernames)
        ).all())
        
        # Import new profiles
        imported = 0
        for username in usernames:
            if username not in existing:
                profile = Profile(username=username, niche_id=niche_id)
                profile.save()
                imported += 1
        
        return {
            'imported': imported,
            'skipped': len(usernames) - imported
        }
