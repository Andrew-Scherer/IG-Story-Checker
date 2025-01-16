"""Initial database schema

Revision ID: 001_initial_schema
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create niches table
    op.create_table(
        'niches',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('order', sa.Integer, nullable=False, default=0),
        sa.Column('daily_story_target', sa.Integer, nullable=False, default=20),
        sa.Column('total_profiles', sa.Integer, default=0),
        sa.Column('active_profiles', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create profiles table
    op.create_table(
        'profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(30), unique=True, nullable=False),
        sa.Column('url', sa.String(255), unique=True, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('niche_id', sa.String(36), sa.ForeignKey('niches.id')),
        sa.Column('last_checked', sa.DateTime),
        sa.Column('last_detected', sa.DateTime),
        sa.Column('total_checks', sa.Integer, default=0),
        sa.Column('total_detections', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create batches table
    op.create_table(
        'batches',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('niche_id', sa.String(36), sa.ForeignKey('niches.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('start_time', sa.DateTime),
        sa.Column('end_time', sa.DateTime),
        sa.Column('total_profiles', sa.Integer, default=0),
        sa.Column('completed_profiles', sa.Integer, default=0),
        sa.Column('successful_checks', sa.Integer, default=0),
        sa.Column('failed_checks', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create batch_profiles table
    op.create_table(
        'batch_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('batch_id', sa.String(36), sa.ForeignKey('batches.id'), nullable=False),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('profiles.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('has_story', sa.Boolean, default=False),
        sa.Column('error', sa.String(255)),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create story_results table
    op.create_table(
        'story_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('profiles.id'), nullable=False),
        sa.Column('batch_id', sa.String(36), sa.ForeignKey('batches.id'), nullable=False),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('screenshot_url', sa.String(255)),
        sa.Column('metadata', sa.JSON),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create proxies table
    op.create_table(
        'proxies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('username', sa.String(255)),
        sa.Column('password', sa.String(255)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_working', sa.Boolean, default=False),
        sa.Column('last_used', sa.DateTime),
        sa.Column('last_tested', sa.DateTime),
        sa.Column('error', sa.String(255)),
        sa.Column('total_requests', sa.Integer, default=0),
        sa.Column('failed_requests', sa.Integer, default=0),
        sa.Column('average_response_time', sa.Float),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer, primary_key=True, default=1),
        sa.Column('profiles_per_minute', sa.Integer, default=30),
        sa.Column('max_threads', sa.Integer, default=3),
        sa.Column('default_batch_size', sa.Integer, default=100),
        sa.Column('story_retention_hours', sa.Integer, default=24),
        sa.Column('auto_trigger_enabled', sa.Boolean, default=True),
        sa.Column('min_trigger_interval', sa.Integer, default=60),
        sa.Column('proxy_test_timeout', sa.Integer, default=10),
        sa.Column('proxy_max_failures', sa.Integer, default=3),
        sa.Column('notifications_enabled', sa.Boolean, default=True),
        sa.Column('notification_email', sa.String(255)),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Create indexes
    op.create_index('ix_profiles_username', 'profiles', ['username'])
    op.create_index('ix_profiles_niche_id', 'profiles', ['niche_id'])
    op.create_index('ix_profiles_status', 'profiles', ['status'])
    op.create_index('ix_profiles_last_checked', 'profiles', ['last_checked'])
    
    op.create_index('ix_batches_niche_id', 'batches', ['niche_id'])
    op.create_index('ix_batches_status', 'batches', ['status'])
    
    op.create_index('ix_batch_profiles_batch_id', 'batch_profiles', ['batch_id'])
    op.create_index('ix_batch_profiles_profile_id', 'batch_profiles', ['profile_id'])
    
    op.create_index('ix_story_results_profile_id', 'story_results', ['profile_id'])
    op.create_index('ix_story_results_expires_at', 'story_results', ['expires_at'])
    
    op.create_index('ix_proxies_is_active', 'proxies', ['is_active'])
    op.create_index('ix_proxies_last_used', 'proxies', ['last_used'])

def downgrade():
    # Drop tables in reverse order
    op.drop_table('system_settings')
    op.drop_table('proxies')
    op.drop_table('story_results')
    op.drop_table('batch_profiles')
    op.drop_table('batches')
    op.drop_table('profiles')
    op.drop_table('niches')
