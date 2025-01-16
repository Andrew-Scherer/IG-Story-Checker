"""
Batch API Resources
Handles batch processing endpoints
"""

from flask import request
from flask_restful import Resource, reqparse, fields, marshal_with, abort
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from models import db, Batch, BatchProfile, Profile, Niche, StoryResult, SystemSettings

# Response fields
batch_fields = {
    'id': fields.String,
    'niche_id': fields.String,
    'status': fields.String,
    'start_time': fields.DateTime(dt_format='iso8601'),
    'end_time': fields.DateTime(dt_format='iso8601'),
    'total_profiles': fields.Integer,
    'completed_profiles': fields.Integer,
    'successful_checks': fields.Integer,
    'failed_checks': fields.Integer,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601')
}

story_result_fields = {
    'id': fields.String,
    'profile_id': fields.String,
    'batch_id': fields.String,
    'detected_at': fields.DateTime(dt_format='iso8601'),
    'expires_at': fields.DateTime(dt_format='iso8601'),
    'screenshot_url': fields.String,
    'metadata': fields.Raw
}

# Request parsers
batch_parser = reqparse.RequestParser()
batch_parser.add_argument('niche_id', type=str, required=True, help='Niche ID is required')
batch_parser.add_argument('profile_count', type=int, default=100)

filter_parser = reqparse.RequestParser()
filter_parser.add_argument('status', type=str, choices=('active', 'completed', 'cancelled'))
filter_parser.add_argument('niche_id', type=str)

class BatchListResource(Resource):
    """Resource for managing batch collections"""
    
    @marshal_with(batch_fields)
    def get(self):
        """Get batches with optional filtering"""
        args = filter_parser.parse_args()
        query = Batch.query
        
        if args.get('status') == 'active':
            query = query.filter(Batch.status.in_(['pending', 'running']))
        elif args.get('status'):
            query = query.filter_by(status=args['status'])
        
        if args.get('niche_id'):
            query = query.filter_by(niche_id=args['niche_id'])
        
        return query.order_by(Batch.created_at.desc()).all()

    @marshal_with(batch_fields)
    def post(self):
        """Create new batch"""
        args = batch_parser.parse_args()
        
        # Validate niche
        niche = Niche.get_by_id(args['niche_id'])
        if not niche:
            abort(400, message=f"Invalid niche ID: {args['niche_id']}")
        
        # Check for existing active batch
        active_batch = Batch.query.filter(
            Batch.niche_id == args['niche_id'],
            Batch.status.in_(['pending', 'running'])
        ).first()
        if active_batch:
            abort(400, message=f"Batch already in progress for niche {args['niche_id']}")
        
        # Get profiles for batch
        profiles = Profile.query.filter(
            Profile.niche_id == args['niche_id'],
            Profile.status == 'active'
        ).order_by(
            Profile.last_checked.asc().nullsfirst()
        ).limit(args['profile_count']).all()
        
        if not profiles:
            abort(400, message=f"No profiles available for niche {args['niche_id']}")
        
        # Create batch
        batch = Batch(niche_id=args['niche_id'])
        batch.save()
        
        # Add profiles to batch
        for profile in profiles:
            BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
        
        batch.update_stats()
        return batch, 201

class BatchResource(Resource):
    """Resource for managing individual batches"""
    
    @marshal_with(batch_fields)
    def get(self, batch_id):
        """Get specific batch"""
        batch = Batch.get_by_id(batch_id)
        if not batch:
            abort(404, message=f"Batch {batch_id} not found")
        return batch

    @marshal_with(batch_fields)
    def post(self, batch_id, action):
        """Handle batch actions"""
        batch = Batch.get_by_id(batch_id)
        if not batch:
            abort(404, message=f"Batch {batch_id} not found")
        
        if action == 'cancel':
            if batch.status not in ['pending', 'running']:
                abort(400, message=f"Cannot cancel batch in {batch.status} status")
            
            batch.status = 'cancelled'
            batch.end_time = datetime.utcnow()
            batch.save()
            return batch
        
        abort(400, message=f"Invalid action: {action}")

class BatchResultsResource(Resource):
    """Resource for managing batch results"""
    
    @marshal_with(story_result_fields)
    def get(self, batch_id):
        """Get story results for batch"""
        batch = Batch.get_by_id(batch_id)
        if not batch:
            abort(404, message=f"Batch {batch_id} not found")
        
        return StoryResult.query.filter_by(batch_id=batch_id).all()

class BatchProgressResource(Resource):
    """Resource for batch progress tracking"""
    
    def get(self, batch_id):
        """Get batch progress details"""
        batch = Batch.get_by_id(batch_id)
        if not batch:
            abort(404, message=f"Batch {batch_id} not found")
        
        stats = db.session.query(
            db.func.count(BatchProfile.id).label('total'),
            db.func.sum(db.case([(BatchProfile.status == 'completed', 1)], else_=0)).label('completed'),
            db.func.sum(db.case([(BatchProfile.has_story == True, 1)], else_=0)).label('successful'),
            db.func.sum(db.case([(BatchProfile.status == 'pending', 1)], else_=0)).label('pending')
        ).filter(BatchProfile.batch_id == batch_id).first()
        
        return {
            'total_profiles': stats.total or 0,
            'completed_profiles': stats.completed or 0,
            'successful_checks': stats.successful or 0,
            'pending_profiles': stats.pending or 0
        }

class BatchAutoTriggerResource(Resource):
    """Resource for automatic batch triggering"""
    
    @marshal_with(batch_fields)
    def post(self):
        """Auto-trigger batches for niches below target"""
        settings = SystemSettings.get_settings()
        if not settings.auto_trigger_enabled:
            return {'triggered': []}
        
        triggered = []
        for niche in Niche.query.all():
            # Skip if active batch exists
            if Batch.query.filter(
                Batch.niche_id == niche.id,
                Batch.status.in_(['pending', 'running'])
            ).first():
                continue
            
            # Check current story count
            current_stories = StoryResult.query.join(
                Profile, StoryResult.profile_id == Profile.id
            ).filter(
                Profile.niche_id == niche.id,
                StoryResult.expires_at > datetime.utcnow()
            ).count()
            
            # Trigger batch if below target
            if current_stories < niche.daily_story_target:
                batch = Batch(niche_id=niche.id)
                batch.save()
                
                # Add profiles
                profiles = Profile.query.filter(
                    Profile.niche_id == niche.id,
                    Profile.status == 'active'
                ).order_by(
                    Profile.last_checked.asc().nullsfirst()
                ).limit(settings.default_batch_size).all()
                
                for profile in profiles:
                    BatchProfile(batch_id=batch.id, profile_id=profile.id).save()
                
                batch.update_stats()
                triggered.append(batch)
        
        return {'triggered': triggered}

class BatchCleanupResource(Resource):
    """Resource for batch cleanup"""
    
    def post(self):
        """Clean up old completed batches"""
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        # Find old completed batches
        old_batches = Batch.query.filter(
            Batch.status == 'completed',
            Batch.end_time < cutoff
        )
        
        count = old_batches.count()
        
        # Delete batch profiles and batches
        BatchProfile.query.filter(
            BatchProfile.batch_id.in_(b.id for b in old_batches)
        ).delete(synchronize_session=False)
        
        old_batches.delete(synchronize_session=False)
        db.session.commit()
        
        return {'cleaned': count}
